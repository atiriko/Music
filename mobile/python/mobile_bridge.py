"""JSON bridge for the unchanged desktop composition engine inside Pyodide."""
from dataclasses import asdict, replace
import base64
import json
import tempfile
from pathlib import Path
from generator import Settings, generate, KEYS, SCALES, COMPLEXITIES, MELODY_STYLES
from Instruments import SOUNDFONT_PROGRAMS, DRUM_KITS
from accompaniment import CHORD_STYLES, BASS_STYLES, VOICINGS, STRUMS
from phrasing import PHRASINGS
from performance import FEELS
from drum_patterns import DRUM_STYLES, DRUM_COMPLEXITIES, DRUM_FILLS
from song import Song, Section, midi_preview, export_song_midi
from midi_export import save_midi
import soundbanks
from mix_settings import MIX_PROFILES
from presets import SOUND_PRESETS
from auto_song import create, add_to_song, LENGTHS, STYLES

DEFAULT_INSTRUMENTS = {'Melody':'Studio Upright','Chords':'Studio Clean Guitar','Bass':'Finger Bass','Drums':'Room kit','Countermelody':'Flute'}


def project_from_dict(data):
    if data.get('version') != 1:
        raise ValueError('Unsupported song project version.')
    if not isinstance(data.get('bpm'),int) or isinstance(data.get('bpm'),bool):
        raise ValueError('Song tempo must be a whole number.')
    sections={name:Section(name,Settings(**section['settings']),section['instruments'])
              for name,section in data['sections'].items()}
    song=Song(int(data['bpm']),sections,list(data['sequence']),data.get('metadata',{}))
    song.validate(allow_empty=True)
    return song


def project_to_dict(song):
    return {'version':1,'bpm':song.bpm,'sequence':song.sequence,'metadata':song.metadata,
            'sections':{name:{'settings':asdict(section.settings),'instruments':section.instruments}
                        for name,section in song.sections.items()}}


def midi_bytes(writer):
    with tempfile.NamedTemporaryFile(suffix='.mid',delete=False) as temporary:
        path=Path(temporary.name)
    try:
        writer(path)
        return base64.b64encode(path.read_bytes()).decode('ascii')
    finally:
        path.unlink(missing_ok=True)


def rhythm(notes):
    return [(round(note.beat,6),note.pitch) for note in notes if note.part=='Drums']


def handle(request_json):
    request=json.loads(request_json)
    action=request['action']
    data=request.get('data',{})
    if action=='catalog':
        result={'keys':KEYS,'scales':list(SCALES),'complexities':COMPLEXITIES,
                'instruments':list(SOUNDFONT_PROGRAMS),'kits':list(DRUM_KITS),
                'drumStyles':DRUM_STYLES,'drumComplexities':DRUM_COMPLEXITIES,
                'chordStyles':CHORD_STYLES,'bassStyles':BASS_STYLES,'feels':FEELS,'phrasings':PHRASINGS,
                'drumFills':list(DRUM_FILLS),'defaults':asdict(Settings()),
                'defaultInstruments':DEFAULT_INSTRUMENTS, 'instrumentGroups':soundbanks.groups(),
                'kitGroups':soundbanks.groups(True),'families':list(soundbanks.FAMILIES),
                'libraries':list(soundbanks.LIBRARIES.values()),'mixProfiles':MIX_PROFILES,
                'songLengths':LENGTHS,'songStyles':STYLES,'voicings':VOICINGS,'strums':STRUMS,
                'melodyStyles':MELODY_STYLES,'soundPresets':SOUND_PRESETS}
    elif action=='register_library':
        result=soundbanks.register(soundbanks.relocate(data))
    elif action=='unregister_library':
        soundbanks.unregister(data['id'])
        result={'removed':data['id']}
    elif action=='automatic_song':
        generated=create(Settings(**data['settings']),data['instruments'],
                         data.get('length','Standard'),data.get('style','From generator'),data.get('candidates',4))
        result=project_to_dict(add_to_song(project_from_dict(data['existing']),generated) if data.get('existing') else generated)
    elif action in ('section','variation'):
        settings=Settings(**data['settings'])
        instruments=dict(data['instruments'])
        Section('Section',settings,instruments)  # Validate the instrument selections too.
        notes=generate(settings,instruments)
        if action=='variation':
            previous=rhythm(generate(replace(settings,feel='Tight')))
            seed=int(data['seed']) % 1_000_000_000
            for attempt in range(32):
                candidate=replace(settings,seed=(seed+attempt*7919)%1_000_000_000)
                candidate_notes=generate(candidate,instruments)
                if rhythm(generate(replace(candidate,feel='Tight')))!=previous:
                    settings,notes=candidate,candidate_notes
                    break
        result={'settings':asdict(settings),'bpm':settings.bpm,'bars':settings.bars,
                'notes':[asdict(note) for note in notes if instruments.get(note.part) is not None],
                'midi':midi_bytes(lambda path:save_midi(path,notes,settings,instruments)),
                'boundaries':[[0,'Section']],'mixProfile':settings.mix_profile,
                'libraries':sorted({soundbanks.voice(name,part=='Drums')['library'] for part,name in instruments.items() if name})}
    elif action=='song':
        song=project_from_dict(data)
        song.validate()
        notes,boundaries=midi_preview(song)
        result={'bpm':song.bpm,'bars':song.bars,'notes':[asdict(note) for note in notes],
                'boundaries':boundaries,'midi':midi_bytes(lambda path:export_song_midi(song,path)),
                'mixProfile':next((section.settings.mix_profile for section in song.sections.values()),'Balanced'),
                'libraries':sorted({soundbanks.voice(name,part=='Drums')['library'] for section in song.sections.values() for part,name in section.instruments.items() if name})}
    elif action=='validate_project':
        result=project_to_dict(project_from_dict(data))
    else:
        raise ValueError('Unknown mobile engine action.')
    return json.dumps(result)


def import_binary(data, filename, family='Auto'):
    """Return metadata and the bank-remapped SF2 bytes the device must store and play."""
    metadata, modified = soundbanks.prepare(data, filename, family)
    soundbanks.register(metadata)
    return json.dumps(metadata), modified
