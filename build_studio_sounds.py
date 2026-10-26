"""Rebuild small electronic patches and a heavy guitar from bundled CC0 sources.

The synth patches use generated periodic waveforms, envelopes, and SF2 filters.
The metal guitar is a driven derivative of the credited FreePats clean guitar.
No external synthesizer or running plugin is needed.
"""
import json
from pathlib import Path
import struct
import numpy as np
from soundbanks import prepare, register, _chunks

ROOT = Path(__file__).parent / 'assets/soundfonts/featured'


def chunk(tag, data):
    return tag + struct.pack('<I', len(data)) + data + (b'\0' if len(data) % 2 else b'')


def name20(text):
    return text.encode('ascii')[:19].ljust(20, b'\0')


def synth_font():
    patches = [('Reese Bass', 38), ('Acid Bass', 38), ('Techno Stab', 81),
               ('DnB Sub', 38), ('Metal Lead', 80), ('Dark Pad', 89)]
    phdr, pbag, pgen, inst, ibag, igen, shdr = [bytearray() for _ in range(7)]
    samples = []
    sample_offset = 0
    gen_index = 0
    rate, period = 22050, 169
    phase = np.arange(period * 16) / period * 2 * np.pi
    slow = np.sin(phase / 16)
    saw = sum(np.sin(phase * h) / h for h in range(1, 20))
    square = sum(np.sin(phase * h) / h for h in range(1, 20, 2))
    waves = [sum(np.sin(phase * h + .4 * slow) / h for h in range(1, 18)) +
             sum(np.sin(phase * h - .4 * slow) / h for h in range(1, 18)),
             saw, .7 * square + .3 * saw, np.sin(phase) + .12 * np.sin(phase * 2),
             np.tanh(2 * saw), np.sin(phase) + .25 * np.sin(phase * 3 + slow)]
    for index, ((title, gm), wave) in enumerate(zip(patches, waves)):
        phdr.extend(struct.pack('<20sHHHIII', name20(title), gm, 0, index, 0, 0, 0))
        pbag.extend(struct.pack('<HH', index, 0))
        pgen.extend(struct.pack('<HH', 41, index))
        inst.extend(struct.pack('<20sH', name20(title), index))
        ibag.extend(struct.pack('<HH', gen_index, 0))
        generators = [(8, 7800 if index in (0, 1, 5) else 11000), (9, 100 if index == 1 else 0),
                      (34, -2500 if index == 5 else -10000), (36, -2200),
                      (37, 250 if index == 2 else 50), (38, -1500 if index == 5 else -3500),
                      (54, 1), (58, 48), (53, index)]
        for operator, value in generators:
            igen.extend(struct.pack('<HH', operator, value & 65535))
        gen_index += len(generators)
        pcm = (wave / max(1, np.abs(wave).max()) * 24575).astype('<i2')
        length = len(pcm)
        shdr.extend(struct.pack('<20sIIIIIBbHH', name20(title), sample_offset, sample_offset + length,
                                sample_offset, sample_offset + length, rate, 48, 0, 0, 1))
        samples.append(pcm.tobytes() + bytes(46 * 2))
        sample_offset += length + 46
    count = len(patches)
    phdr.extend(struct.pack('<20sHHHIII', name20('EOP'), 0, 0, count, 0, 0, 0))
    pbag.extend(struct.pack('<HH', count, 0)); pgen.extend(bytes(4))
    inst.extend(struct.pack('<20sH', name20('EOI'), count))
    ibag.extend(struct.pack('<HH', gen_index, 0)); igen.extend(bytes(4))
    shdr.extend(struct.pack('<20sIIIIIBbHH', name20('EOS'), sample_offset, sample_offset,
                            sample_offset, sample_offset, rate, 0, 0, 0, 1))
    info = chunk(b'LIST', b'INFO' + chunk(b'ifil', struct.pack('<HH', 2, 1)) + chunk(b'INAM', b'Music Studio Synths\0'))
    sdta = chunk(b'LIST', b'sdta' + chunk(b'smpl', b''.join(samples)))
    pdta = chunk(b'LIST', b'pdta' + b''.join(chunk(tag, data) for tag, data in [
        (b'phdr', phdr), (b'pbag', pbag), (b'pmod', bytes(10)), (b'pgen', pgen),
        (b'inst', inst), (b'ibag', ibag), (b'imod', bytes(10)), (b'igen', igen), (b'shdr', shdr)]))
    payload = b'sfbk' + info + sdta + pdta
    return b'RIFF' + struct.pack('<I', len(payload)) + payload


def main():
    catalog = json.loads((ROOT / 'catalog.json').read_text())
    clean = next(ROOT.glob('EGuitarFSBS*/EGuitarFSBS*.sf2'))
    metal = bytearray(clean.read_bytes())
    for tag, start, end in _chunks(metal, 12, len(metal)):
        if tag == b'LIST' and metal[start:start + 4] == b'sdta':
            for child, at, stop in _chunks(metal, start + 4, end):
                if child == b'smpl':
                    pcm = np.frombuffer(metal, dtype='<i2', count=(stop - at) // 2, offset=at)
                    pcm[:] = (np.tanh(pcm.astype(np.float32) / 32768 * 6) * 26000).astype('<i2')
    sources = [(bytes(metal), 'metal-guitar.sf2', 'Studio Metal Guitar', 'Guitars'),
               (synth_font(), 'studio-synths.sf2', 'Studio Synths', 'Auto')]
    for data, filename, title, family in sources:
        meta, normalized = prepare(data, filename, family, title)
        if title == 'Studio Synths':
            for preset in meta['presets']:
                preset['label'] = preset['name']
        else:
            for preset in meta['presets']:
                preset['label'] = title
                preset['gm_program'] = 30
        meta['relative_file'] = (ROOT / filename).relative_to(Path(__file__).parent).as_posix()
        (ROOT / filename).write_bytes(normalized)
        register(meta)
        catalog = [entry for entry in catalog if entry['id'] != meta['id']] + [meta]
        print(title, len(normalized), 'bytes')
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, indent=2))
    (ROOT / 'STUDIO-SOUNDS.txt').write_text('Studio Metal Guitar is a driven derivative of the CC0 FreePats FSBS clean guitar. See the original credits and license.\nStudio Synths contains mathematically generated waveforms and no third-party recordings. Rebuild with build_studio_sounds.py.\n')


if __name__ == '__main__':
    main()
