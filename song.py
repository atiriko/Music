"""Song sections, arrangement compilation, project persistence, and WAV/MIDI export."""
from dataclasses import asdict, dataclass, field, replace
import io
import json
from pathlib import Path
import re
import wave
import numpy as np
import main as engine
from Event import Event
from Sheduler import Sheduler
from generator import Settings, Note, generate
from Instruments import SOUNDFONT_PROGRAMS, DRUM_KITS
from midi_export import save_midi_clips

FILL = '[Drum fill]'

@dataclass(frozen=True)
class Section:
    name: str
    settings: Settings
    instruments: dict

    def __post_init__(self):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _-]{0,31}', self.name):
            raise ValueError('Use a section name of up to 32 letters, numbers, spaces, underscores, or hyphens.')
        for part, voice in self.instruments.items():
            if part not in ('Melody', 'Chords', 'Bass', 'Drums'):
                raise ValueError('Unknown song part')
            if voice is not None and voice not in (DRUM_KITS if part == 'Drums' else SOUNDFONT_PROGRAMS):
                raise ValueError('Unknown song instrument')

@dataclass
class Song:
    bpm: int = 110
    sections: dict = field(default_factory=dict)
    sequence: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def bars(self):
        return sum(1 if name == FILL else self.sections[name].settings.bars for name in self.sequence)

    def validate(self, allow_empty=False):
        if not 40 <= self.bpm <= 220:
            raise ValueError('Song tempo must be 40-220 BPM.')
        if not self.sequence and not allow_empty:
            raise ValueError('Add sections to the song sequence first.')
        if len(self.sequence) > 128 or len(self.sections) > 32:
            raise ValueError('Songs support up to 32 sections and 128 sequence entries.')
        if any(name != FILL and name not in self.sections for name in self.sequence):
            raise ValueError('Song sequence refers to a missing section.')
        if not (0 if allow_empty else 1) <= self.bars <= 256:
            raise ValueError('A song must contain 1-256 bars.')

    def save(self, path):
        self.validate(allow_empty=True)
        payload = {'version': 1, 'bpm': self.bpm, 'sequence': self.sequence, 'metadata': self.metadata,
                   'sections': {name: {'settings': asdict(section.settings), 'instruments': section.instruments}
                                for name, section in self.sections.items()}}
        Path(path).write_text(json.dumps(payload, indent=2), encoding='utf-8')

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if data.get('version') != 1:
            raise ValueError('Unsupported song project version.')
        sections = {name: Section(name, Settings(**value['settings']), value['instruments'])
                    for name, value in data['sections'].items()}
        song = cls(int(data['bpm']), sections, list(data['sequence']), data.get('metadata', {}))
        song.validate(allow_empty=True)
        return song

@dataclass(frozen=True)
class Clip:
    name: str
    start_beat: float
    settings: Settings
    notes: list
    instruments: dict


def compile_song(song):
    song.validate()
    offset = 0
    clips = []
    cache = {}
    kit = 'Standard kit'
    drum_style = 'Rock'
    previous_seed = 0
    for index, name in enumerate(song.sequence):
        if name == FILL:
            fill_seed = (previous_seed * 1009 + 10000 + index) % 1_000_000_000
            settings = Settings(bpm=song.bpm, bars=1, complexity='Intricate', seed=fill_seed,
                                drum_style=drum_style)
            scheduler = Sheduler(engine.Tempo(song.bpm), None)
            engine.generateDrums(scheduler, 1, 2, np.random.default_rng(settings.seed), style=drum_style, fill_every=0)
            for beat, pitch in zip((2, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75), (38, 38, 50, 50, 47, 47, 45, 45)):
                scheduler.addEvent(Event(9, pitch, beat * scheduler.tempo.quarter, .15 * scheduler.tempo.quarter, 92))
            notes = [Note('Drums', event.note, event.time / scheduler.tempo.quarter,
                          event.length / scheduler.tempo.quarter, event.velocity / 127) for event in sorted(scheduler.queue)]
            instruments = {'Drums': kit}
        else:
            section = song.sections[name]
            settings = replace(section.settings, bpm=song.bpm)
            if name not in cache:
                cache[name] = generate(settings, section.instruments)
            notes = cache[name]
            instruments = section.instruments
            kit = instruments.get('Drums') or kit
            drum_style = settings.drum_style
            previous_seed = settings.seed
        clips.append(Clip(name, offset, settings, notes, instruments))
        offset += settings.bars * 4
    return clips


def midi_preview(song):
    """The audible/exported notes on the full song timeline, in MIDI beats."""
    clips = compile_song(song)
    notes = [replace(note, beat=note.beat + clip.start_beat)
             for clip in clips for note in clip.notes if clip.instruments.get(note.part) is not None]
    boundaries = [(clip.start_beat, clip.name) for clip in clips]
    return sorted(notes, key=lambda note: (note.beat, note.part, note.pitch)), boundaries


def render_song(song, cancelled=None, progress=None):
    # Keep composition/project/MIDI APIs portable; only desktop WAV rendering
    # needs the platform-specific TinySoundFont Python extension.
    from synth import SAMPLE_RATE, render
    clips = compile_song(song)
    frames = round((song.bars * 4 * 60 / song.bpm + 1) * SAMPLE_RATE)
    mix = np.zeros((frames, 2), dtype=np.float32)
    cached = {}
    for index, clip in enumerate(clips):
        if cancelled is not None and cancelled.is_set():
            return None
        key = clip.name if clip.name != FILL else (clip.name, index)
        if key not in cached:
            audio = render(clip.notes, clip.settings, clip.instruments, cancelled, master=False)
            if audio is None:
                return None
            with wave.open(io.BytesIO(audio), 'rb') as wav:
                cached[key] = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').reshape(-1, 2).astype(np.float32) / 32768
        samples = cached[key]
        start = round(clip.start_beat * 60 / song.bpm * SAMPLE_RATE)
        size = min(len(samples), frames - start)
        mix[start:start + size] += samples[:size]
        if progress:
            progress(index + 1, len(clips))
    from production import finish
    profile = next((clip.settings.mix_profile for clip in clips if clip.name != FILL), 'Balanced')
    mix = finish(mix, SAMPLE_RATE, profile)
    peak = float(np.max(np.abs(mix)))
    if peak > .95:
        mix *= .95 / peak
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes((mix * 32767).astype('<i2').tobytes())
    return output.getvalue()


def export_song_midi(song, path):
    clips = compile_song(song)
    save_midi_clips(path, [(clip.start_beat, clip.notes, clip.instruments, clip.settings.mix_profile) for clip in clips], song.bpm, song.bars * 4)
