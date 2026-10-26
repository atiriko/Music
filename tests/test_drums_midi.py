import io
import tempfile
from pathlib import Path
import unittest
import wave
import numpy as np
from mido import MidiFile
from generator import Settings, generate, COMPLEXITIES
from Instruments import DRUM_KITS, SOUNDFONT_PROGRAMS
from synth import render
from midi_export import save_midi


class DrumAndMidiTests(unittest.TestCase):
    def test_full_instrument_bank(self):
        import soundbanks
        general = [name for name in SOUNDFONT_PROGRAMS if name not in soundbanks.EXTRA]
        self.assertEqual(len(general), 128)
        self.assertEqual({SOUNDFONT_PROGRAMS[name] for name in general}, set(range(128)))
        # Bundled studio instruments are listed in addition to the GM bank.
        self.assertIn('Studio Upright', SOUNDFONT_PROGRAMS)
        self.assertIn('Studio Clean Guitar', SOUNDFONT_PROGRAMS)

    def test_drums_cover_every_bar_and_complexity(self):
        counts = []
        for complexity in COMPLEXITIES:
            settings = Settings(bars=8, complexity=complexity)
            drums = [note for note in generate(settings) if note.part == 'Drums']
            counts.append(len(drums))
            for bar in range(8):
                hits = [note for note in drums if bar * 4 <= note.beat < (bar + 1) * 4]
                self.assertTrue(any(note.pitch == 36 for note in hits))
                self.assertTrue(any(note.pitch == 38 for note in hits))
                self.assertTrue(any(note.pitch == 42 for note in hits))
            self.assertTrue(all(35 <= note.pitch <= 81 for note in drums))
        self.assertLess(counts[0], counts[1])
        self.assertLess(counts[1], counts[2])

    def test_every_drum_kit_is_audible(self):
        settings = Settings(bars=1, bpm=220)
        notes = generate(settings)
        for kit in DRUM_KITS:
            with self.subTest(kit=kit):
                audio = render(notes, settings, {'Drums': kit})
                with wave.open(io.BytesIO(audio), 'rb') as wav:
                    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
                self.assertGreater(np.max(np.abs(samples)), 100)

    def test_midi_contains_matching_pitches_timing_and_programs(self):
        settings = Settings(bars=8, bpm=137, complexity='Intricate', seed=12)
        notes = generate(settings)
        instruments = {'Melody': 'Piano', 'Chords': 'Strings', 'Bass': 'Synth bass', 'Drums': '808/909 kit'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'arrangement.mid'
            save_midi(path, notes, settings, instruments)
            midi = MidiFile(path)
        self.assertEqual(len(midi.tracks), 5)
        self.assertAlmostEqual(midi.length, 8 * 4 * 60 / 137, places=4)
        for track, (part, channel) in zip(midi.tracks[1:], [('Melody', 0), ('Chords', 1), ('Bass', 2), ('Drums', 9)]):
            program = next(message for message in track if message.type == 'program_change')
            self.assertEqual(program.channel, channel)
            expected_program = (DRUM_KITS if part == 'Drums' else SOUNDFONT_PROGRAMS)[instruments[part]]
            self.assertEqual(program.program, expected_program)
            tick = 0
            actual = []
            offs = 0
            for message in track:
                tick += message.time
                if message.type == 'note_on' and message.velocity:
                    self.assertEqual(message.channel, channel)
                    actual.append((tick, message.note))
                if message.type == 'note_off':
                    offs += 1
            expected = sorted((round(note.beat * midi.ticks_per_beat), note.pitch) for note in notes if note.part == part)
            self.assertEqual(sorted(actual), expected)
            self.assertEqual(offs, len(expected))
            self.assertEqual(tick, 8 * 4 * midi.ticks_per_beat)

    def test_drum_only_midi_and_muted_parts(self):
        settings = Settings(bars=1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'drums.mid'
            save_midi(path, generate(settings), settings, {'Drums': 'Standard kit'})
            midi = MidiFile(path)
        self.assertEqual(len(midi.tracks), 2)
        self.assertTrue(all(message.channel == 9 for track in midi.tracks for message in track if not message.is_meta))


if __name__ == '__main__':
    unittest.main()
