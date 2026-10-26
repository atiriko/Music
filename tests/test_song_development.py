"""User sections survive automation; new musical controls affect the score."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from mido import MidiFile
from generator import Settings, generate, build_scheduler, MELODY_STYLES
from accompaniment import VOICINGS, STRUMS
from auto_song import create, add_to_song
from song import Song, Section, compile_song, export_song_midi
from presets import SOUND_PRESETS
from soundbanks import voice


class SongDevelopmentTests(unittest.TestCase):
    def test_generated_song_preserves_user_sections_and_name_collisions(self):
        instruments = SOUND_PRESETS['Studio band']['instruments']
        custom = Section('Chorus', Settings(seed=99, bars=2), instruments)
        unused = Section('My riff', Settings(seed=42, bars=1), instruments)
        existing = Song(123, {'Chorus': custom, 'My riff': unused}, ['Chorus'], {'custom': 'kept'})
        snapshot = deepcopy(existing)
        generated = create(Settings(seed=11), instruments, 'Short', candidates=1)
        merged = add_to_song(existing, generated)
        self.assertEqual(existing, snapshot)
        self.assertEqual(merged.sections['Chorus'], custom)
        self.assertEqual(merged.sections['My riff'], unused)
        self.assertEqual(merged.sequence[0], 'Chorus')
        self.assertIn('Chorus 2', merged.sections)
        self.assertIn('Chorus 2', merged.sequence[1:])
        self.assertEqual(merged.bpm, 123)
        self.assertEqual(merged.metadata['custom'], 'kept')
        self.assertEqual(merged.bars, existing.bars + generated.bars)

    def test_limit_failure_leaves_existing_song_unchanged(self):
        voices = SOUND_PRESETS['Studio band']['instruments']
        section = Section('Full', Settings(bars=32), voices)
        existing = Song(110, {'Full': section}, ['Full'] * 8)
        snapshot = deepcopy(existing)
        generated = create(Settings(), voices, 'Short', candidates=1)
        with self.assertRaises(ValueError):
            add_to_song(existing, generated)
        self.assertEqual(existing, snapshot)

    def test_voicings_and_strums_are_different_and_in_key(self):
        signatures = set()
        for voicing in VOICINGS:
            settings = Settings(chord_voicing=voicing, bars=2, seed=2, feel='Tight', phrasing='Continuous')
            scheduler = build_scheduler(settings)
            signatures.add(scheduler.harmony[0][3])
            for note in generate(settings):
                if note.part != 'Drums':
                    self.assertIn(note.pitch % 12, (0, 2, 4, 5, 7, 9, 11))
        self.assertGreaterEqual(len(signatures), 7)
        signatures = set()
        for pattern in STRUMS[1:]:
            notes = generate(Settings(strum_pattern=pattern, bars=1, feel='Tight', phrasing='Continuous'))
            signatures.add(tuple((n.beat, n.duration, n.pitch) for n in notes if n.part == 'Chords'))
        self.assertEqual(len(signatures), len(STRUMS) - 1)

    def test_second_melody_is_optional_diatonic_and_exported_separately(self):
        voices = SOUND_PRESETS['Studio band']['instruments']
        self.assertFalse(any(n.part == 'Countermelody' for n in generate(Settings(), voices)))
        settings = Settings(countermelody=True, seed=9)
        notes = generate(settings, voices)
        lead = [n for n in notes if n.part == 'Melody']
        counter = [n for n in notes if n.part == 'Countermelody']
        self.assertTrue(counter)
        self.assertLess(len(counter), len(lead))
        self.assertTrue(all(n.pitch % 12 in (0, 2, 4, 5, 7, 9, 11) for n in counter))
        song = Song(110, {'Both': Section('Both', settings, voices)}, ['Both'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'counterpoint.mid'
            export_song_midi(song, path)
            midi = MidiFile(path)
        track = next(t for t in midi.tracks if t.name.startswith('Countermelody'))
        self.assertTrue(all(m.channel == 3 for m in track if not m.is_meta))

    def test_melody_characters_and_seeds_develop_distinct_motifs(self):
        signatures = set()
        for style in MELODY_STYLES:
            for seed in range(8):
                notes = [n for n in generate(Settings(melody_style=style, seed=seed, feel='Tight')) if n.part == 'Melody']
                signatures.add(tuple((n.beat, n.pitch % 12) for n in notes))
        self.assertGreater(len(signatures), 32)

    def test_heavy_and_electronic_presets_resolve_and_select_real_patterns(self):
        for name in ('Metal', 'Drum and bass', 'Techno'):
            preset = SOUND_PRESETS[name]
            for part, selected in preset['instruments'].items():
                self.assertIn('program', voice(selected, part == 'Drums'))
            settings = Settings(**preset['settings'], bars=4, seed=4)
            notes = generate(settings, preset['instruments'])
            self.assertGreater(sum(n.part == 'Drums' for n in notes), 30)
            self.assertTrue(all(n.beat + n.duration <= 16 + 1e-7 for n in notes))


if __name__ == '__main__':
    unittest.main()
