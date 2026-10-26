"""Desktop settings and adapter to the original Event/Sheduler engine.

The original main.py entry points delegate accompaniment and performance to
small shared modules. This adapter translates UI settings and scheduled events
into the renderer's beat-based note format.
"""
from dataclasses import dataclass
import numpy as np
import main as engine
import Notes
import soundbanks
from accompaniment import CHORD_STYLES, BASS_STYLES
from performance import FEELS, apply as perform
from registers import arrange
from phrasing import PHRASINGS, apply as phrase, protect_breaks
from Sheduler import Sheduler
from drum_patterns import DRUM_STYLES, DRUM_COMPLEXITIES, DRUM_FILLS

KEYS = ('C', 'C# / Db', 'D', 'D# / Eb', 'E', 'F', 'F# / Gb', 'G', 'G# / Ab', 'A', 'A# / Bb', 'B')
SCALES = {
    'Major': engine.majorScale,
    'Natural minor': engine.minorScale,
    'Harmonic minor': engine.harmonicMinorScale,
    'Dorian': engine.dorianScale,
    'Phrygian': engine.phrygianScale,
    'Lydian': engine.lydianScale,
    'Mixolydian': engine.mixolydianScale,
    'Locrian': engine.locrianScale,
    'Harmonic major': engine.harmonicMajorScale,
    'Melodic minor': engine.melodicMinorScale,
    'Melodic major': engine.melodicMajorScale,
    'Major pentatonic': (0, 2, 4, 7, 9),
    'Minor pentatonic': engine.pentatonicScale,
    'Blues': engine.bluesScale,
    'Whole tone': engine.wholeToneScale,
    'Jazz minor': engine.jazzMinorScale,
    'Jazz major': engine.jazzMajorScale,
    'Bebop': engine.bebopScale,
}
COMPLEXITIES = ('Simple', 'Balanced', 'Intricate')

@dataclass(frozen=True)
class Settings:
    key: str = 'C'
    scale: str = 'Major'
    complexity: str = 'Balanced'
    bpm: int = 110
    bars: int = 8
    seed: int = 1
    drum_style: str = 'Rock'
    drum_complexity: str = 'Follow complexity'
    drum_fills: str = 'Every 4 bars'
    chord_style: str = 'Varied'
    bass_style: str = 'Varied'
    feel: str = 'Natural'
    phrasing: str = 'Balanced'
    hook_seed: int | None = None
    section_role: str = 'Loop'
    energy: int = 65
    mix_profile: str = 'Balanced'

    def __post_init__(self):
        if self.hook_seed is not None and (type(self.hook_seed) is not int or not 0 <= self.hook_seed <= 999999999):
            raise ValueError('Hook seed must be a whole number from 0 to 999999999.')
        if self.section_role not in ('Loop', 'Intro', 'Verse', 'Chorus', 'Bridge', 'Breakdown', 'Outro'):
            raise ValueError('Choose a listed section role.')
        if type(self.energy) is not int or not 0 <= self.energy <= 100:
            raise ValueError('Energy must be a whole number from 0 to 100.')
        from mix_settings import MIX_PROFILES
        if self.mix_profile not in MIX_PROFILES:
            raise ValueError('Choose a listed mix profile.')
        if self.phrasing not in PHRASINGS:
            raise ValueError('Choose a listed phrasing setting.')
        if self.chord_style not in CHORD_STYLES or self.bass_style not in BASS_STYLES or self.feel not in FEELS:
            raise ValueError('Choose a listed chord pattern, bass pattern, and playing feel.')
        if any(not isinstance(value, int) or isinstance(value, bool) for value in (self.bpm, self.bars, self.seed)):
            raise ValueError('Tempo, length, and seed must be whole numbers.')
        if self.key not in KEYS or self.scale not in SCALES or self.complexity not in COMPLEXITIES:
            raise ValueError('Choose a listed key, scale, and complexity.')
        if not 40 <= self.bpm <= 220 or not 1 <= self.bars <= 32:
            raise ValueError('Tempo must be 40-220 BPM and length 1-32 bars.')
        if not 0 <= self.seed <= 999999999:
            raise ValueError('Seed must be 0-999999999.')
        if self.drum_style not in DRUM_STYLES or self.drum_complexity not in DRUM_COMPLEXITIES or self.drum_fills not in DRUM_FILLS:
            raise ValueError('Choose a listed drum style, complexity, and fill frequency.')

@dataclass(frozen=True)
class Note:
    part: str
    pitch: int
    beat: float
    duration: float
    velocity: float

# Retain this public helper as an alias to the original engine's implementation.
scale_pitch = engine.scaleNote


def build_scheduler(settings, midiout=None, instruments=None):
    """Use the same original engine for both built-in audio and external MIDI."""
    tempo = engine.Tempo(settings.bpm)
    scheduler = Sheduler(tempo, midiout)
    key = 48 + KEYS.index(settings.key)
    scale = SCALES[settings.scale]
    level = COMPLEXITIES.index(settings.complexity)
    rng = np.random.default_rng(settings.seed)
    engine.generateChortProgression(key, scale, Notes.Notes(), scheduler,
                                   settings.bars, level, rng, settings.chord_style, settings.bass_style)
    melody_rng = rng if settings.hook_seed is None else np.random.default_rng(settings.hook_seed)
    engine.generateMelody(key + 12, midiout, tempo, scale, 0,
                          settings.bars * tempo.whole, scheduler, level, melody_rng, settings.phrasing)
    drum_level = level if settings.drum_complexity == 'Follow complexity' else COMPLEXITIES.index(settings.drum_complexity)
    drum_rng = np.random.default_rng(np.random.SeedSequence([settings.seed, 0xD12]))
    engine.generateDrums(scheduler, settings.bars, drum_level, drum_rng,
                         settings.drum_style, DRUM_FILLS[settings.drum_fills])
    from arrangement import shape
    from articulation import apply as articulate
    shape(scheduler, settings)
    articulate(scheduler, settings, instruments or {})
    phrase(scheduler, settings.bars, settings.phrasing)
    perform(scheduler, settings.bars, settings.seed, settings.feel)
    protect_breaks(scheduler, settings.bars, settings.phrasing)
    return scheduler


def generate(settings, instruments=None):
    scheduler = build_scheduler(settings, instruments=instruments)
    parts = {0: 'Melody', 1: 'Chords', 2: 'Bass', 9: 'Drums'}
    events = sorted(scheduler.queue)
    notes = [Note(parts[event.channel], event.note,
                 event.time / scheduler.tempo.quarter,
                 event.length / scheduler.tempo.quarter, event.velocity / 127)
            for event in events]
    return arrange(notes, settings.seed, instruments,
                   [event.nominal_time / scheduler.tempo.quarter for event in events])
