"""Instrument catalog and bounded SF2 imports shared by desktop and mobile.

Imported presets receive private MIDI banks so several libraries can play at
once. Preset identifiers contain a content hash; missing libraries fail clearly.
Only the preset headers are changed; sample recordings are left intact.
"""
import hashlib
import json
from pathlib import Path
import struct
from Instruments import SOUNDFONT_PROGRAMS, DRUM_KITS

ROOT = Path(__file__).resolve().parent
USER_DIR = ROOT / 'assets' / 'user-instruments'
MAX_BYTES = 64 * 1024 * 1024
FAMILIES = ('Pianos & keys', 'Mallets & bells', 'Organs', 'Guitars', 'Basses',
            'Solo strings', 'Strings & voices', 'Brass', 'Reeds', 'Flutes & pipes',
            'Synth leads', 'Synth pads', 'Textures & effects', 'World instruments',
            'Percussion', 'Sound effects')
EXTRA = {}
LIBRARIES = {}


def category(name, drums=False):
    if name in EXTRA:
        return EXTRA[name]['category']
    return 'Drum kits' if drums else FAMILIES[SOUNDFONT_PROGRAMS[name] // 8]


def groups(drums=False):
    result = {}
    for name in (DRUM_KITS if drums else SOUNDFONT_PROGRAMS):
        result.setdefault(category(name, drums), []).append(name)
    return result


def voice(name, drums=False):
    if name in EXTRA:
        return EXTRA[name]
    mapping = DRUM_KITS if drums else SOUNDFONT_PROGRAMS
    if name not in mapping:
        raise ValueError('Missing instrument library for: ' + str(name) + '. Import its SF2 file first.')
    return {'program': mapping[name], 'bank': 128 if drums else 0,
            'gm_program': mapping[name], 'library': 'general-user',
            'file': str(ROOT / 'assets/soundfonts/GeneralUser-GS.sf2')}


def _chunks(data, start, end):
    while start + 8 <= end:
        tag = data[start:start + 4]
        size = struct.unpack_from('<I', data, start + 4)[0]
        stop = start + 8 + size
        if stop > end:
            raise ValueError('Invalid SF2 chunk length.')
        yield tag, start + 8, stop
        start = stop + size % 2


def inspect(data):
    if not 1024 <= len(data) <= MAX_BYTES:
        raise ValueError('Use an SF2 file between 1 KB and 64 MB.')
    if data[:4] != b'RIFF' or data[8:12] != b'sfbk':
        raise ValueError('Choose an uncompressed .sf2 SoundFont instrument file.')
    if struct.unpack_from('<I', data, 4)[0] + 8 != len(data):
        raise ValueError('The SF2 file is truncated or has an invalid RIFF length.')
    presets = []
    has_samples = False
    for tag, start, end in _chunks(data, 12, len(data)):
        if tag != b'LIST':
            continue
        kind = data[start:start + 4]
        for child, at, stop in _chunks(data, start + 4, end):
            if kind == b'sdta' and child == b'smpl':
                has_samples = stop > at
            if kind == b'pdta' and child == b'phdr':
                if (stop - at) % 38 or stop - at < 76:
                    raise ValueError('The SF2 preset table is invalid.')
                for offset in range(at, stop - 38, 38):
                    name = data[offset:offset + 20].split(b'\0')[0].decode('latin1').strip()
                    program, bank = struct.unpack_from('<HH', data, offset + 20)
                    presets.append({'name': name or 'Instrument', 'program': program,
                                    'bank': bank, 'offset': offset})
    if not presets or not has_samples or len(presets) > 512:
        raise ValueError('The SF2 needs sample data and 1-512 playable presets.')
    if any(p['program'] > 127 for p in presets):
        raise ValueError('The SF2 has an invalid instrument program.')
    return presets


def register(metadata):
    """Register trusted, previously inspected metadata (also used after restore)."""
    library = metadata['id']
    if library in LIBRARIES:
        return LIBRARIES[library]
    if not isinstance(library, str) or not library.startswith('sf2-'):
        raise ValueError('Invalid instrument library identifier.')
    used = {p['bank'] & 127 for p in EXTRA.values()}
    requested = {p['bank'] & 127 for p in metadata['presets']}
    if used & requested:
        raise ValueError('Instrument bank conflict. Reimport this SF2 file on this device.')
    for preset in metadata['presets']:
        name = preset['label']
        if preset['category'] not in (*FAMILIES, 'Drum kits') or not 0 <= preset['program'] <= 127:
            raise ValueError('Invalid instrument preset metadata.')
        if not 32 <= (preset['bank'] & 127) <= 111:
            raise ValueError('Invalid imported MIDI bank.')
        entry = {**preset, 'library': library, 'file': metadata.get('file', '')}
        EXTRA[name] = entry
        (DRUM_KITS if preset['drums'] else SOUNDFONT_PROGRAMS)[name] = preset['gm_program']
    LIBRARIES[library] = metadata
    return metadata


def unregister(library):
    """Forget an imported library so its instruments leave every picker."""
    metadata = LIBRARIES.pop(library, None)
    if metadata is None:
        return
    for preset in metadata['presets']:
        EXTRA.pop(preset['label'], None)
        (DRUM_KITS if preset['drums'] else SOUNDFONT_PROGRAMS).pop(preset['label'], None)


def prepare(data, filename, family='Auto', title=None):
    presets = inspect(data)
    digest = hashlib.sha256(data).hexdigest()
    identifier = 'sf2-' + digest
    if identifier in LIBRARIES:
        return LIBRARIES[identifier], data
    used = {p['bank'] & 127 for p in EXTRA.values()}
    banks = [b for b in range(32, 112) if b not in used]
    needed = (len(presets) + 127) // 128
    if len(banks) < needed:
        raise ValueError('The imported instrument bank limit has been reached.')
    if family != 'Auto' and family not in FAMILIES:
        raise ValueError('Choose a listed instrument type.')
    title = (title or Path(filename).stem)[:48]
    modified = bytearray(data)
    entries = []
    for index, preset in enumerate(presets):
        drums = bool(preset['bank'] & 128)
        bank = banks[index // 128] | (128 if drums else 0)
        program = index % 128
        chosen_family = 'Drum kits' if drums else family if family != 'Auto' else FAMILIES[preset['program'] // 8]
        gm = preset['program'] if family == 'Auto' or drums else FAMILIES.index(chosen_family) * 8
        label = f"{title} / {preset['name']} [{digest[:8]}:{index}]"
        entries.append({'label': label, 'name': preset['name'], 'category': chosen_family,
                        'program': program, 'bank': bank, 'gm_program': gm,
                        'drums': drums, 'offset': preset['offset']})
        struct.pack_into('<HH', modified, preset['offset'] + 20, program, bank)
    metadata = {'id': identifier, 'name': title, 'filename': Path(filename).name,
                'sha256': digest, 'presets': entries}
    return metadata, bytes(modified)


def import_file(path, family='Auto'):
    source = Path(path)
    if source.stat().st_size > MAX_BYTES:
        raise ValueError('SF2 imports are limited to 64 MB per file.')
    metadata, data = prepare(source.read_bytes(), source.name, family)
    if metadata['id'] in LIBRARIES:
        return metadata
    USER_DIR.mkdir(parents=True, exist_ok=True)
    target = USER_DIR / (metadata['sha256'] + '.sf2')
    target.write_bytes(data)
    metadata['file'] = str(target)
    (USER_DIR / (metadata['sha256'] + '.json')).write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return register(metadata)


def restore():
    manifest = ROOT / 'assets/soundfonts/featured/catalog.json'
    if manifest.exists():
        for entry in json.loads(manifest.read_text(encoding='utf-8')):
            entry['file'] = str(ROOT / entry['relative_file'])
            register(entry)
    if USER_DIR.exists():
        for path in sorted(USER_DIR.glob('*.json')):
            entry = json.loads(path.read_text(encoding='utf-8'))
            if Path(entry['file']).is_file():
                register(entry)


restore()
