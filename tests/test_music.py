import io
import threading
import unittest
import wave
import numpy as np
from generator import KEYS, SCALES, COMPLEXITIES, Settings, generate, scale_pitch
from synth import INSTRUMENTS, SAMPLE_RATE, render


class CompositionTests(unittest.TestCase):
    def test_every_note_stays_in_selected_scale(self):
        for tonic, key in enumerate(KEYS):
            for name, scale in SCALES.items():
                for complexity in COMPLEXITIES:
                    for seed in range(5):
                        settings = Settings(key, name, complexity, bars=4, seed=seed)
                        with self.subTest(key=key, scale=name, complexity=complexity, seed=seed):
                            notes = generate(settings)
                            self.assertEqual({n.part for n in notes}, {'Melody', 'Chords', 'Bass', 'Drums'})
                            for n in notes:
                                if n.part != 'Drums':
                                    self.assertIn((n.pitch - tonic) % 12, scale)
                                self.assertTrue(0 <= n.pitch <= 127)
                                self.assertTrue(0 <= n.beat < 16)
                                self.assertTrue(0 < n.duration <= 16 - n.beat)

    def test_minor_and_diminished_chord_regressions(self):
        minor = SCALES['Natural minor']
        self.assertEqual([scale_pitch(60, minor, d) for d in (0, 2, 4)], [60, 63, 67])
        major = SCALES['Major']
        self.assertEqual([scale_pitch(60, major, d) for d in (6, 8, 10)], [71, 74, 77])

    def test_reproducible_and_different_variations(self):
        self.assertEqual(generate(Settings(seed=123)), generate(Settings(seed=123)))
        self.assertNotEqual(generate(Settings(seed=123)), generate(Settings(seed=124)))

    def test_complexity_increases_activity(self):
        counts = [sum(len(generate(Settings(complexity=c, seed=s))) for s in range(20)) for c in COMPLEXITIES]
        self.assertLess(counts[0], counts[1])
        self.assertLess(counts[1], counts[2])

    def test_invalid_controls(self):
        for kwargs in ({'bpm': 0}, {'bpm': 221}, {'bars': 0}, {'bars': 33}, {'key': 'H'}, {'scale': 'Other'}):
            with self.assertRaises(ValueError):
                Settings(**kwargs)


class AudioTests(unittest.TestCase):
    def test_instrument_choices_change_the_rendered_sound(self):
        settings = Settings(bars=1)
        notes = generate(settings)
        sounds = [render(notes, settings, {'Melody': voice}) for voice in INSTRUMENTS]
        self.assertEqual(len(set(sounds)), len(INSTRUMENTS))

    def test_every_instrument_renders_valid_audible_wav(self):
        settings = Settings(bars=1, bpm=220)
        notes = generate(settings)
        for instrument in INSTRUMENTS:
            with self.subTest(instrument=instrument):
                audio = render(notes, settings, dict.fromkeys(('Melody', 'Chords', 'Bass'), instrument))
                with wave.open(io.BytesIO(audio), 'rb') as wav:
                    self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()), (2, 2, SAMPLE_RATE))
                    self.assertAlmostEqual(wav.getnframes() / SAMPLE_RATE, 4 * 60 / 220 + 1, places=4)
                    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
                    self.assertGreater(np.max(np.abs(samples)), 100)
                    self.assertLessEqual(np.max(np.abs(samples)), 31130)
                    self.assertTrue(np.all(samples[-100:] == 0))

    def test_muted_parts_and_cancellation(self):
        settings = Settings(bars=1)
        notes = generate(settings)
        audio = render(notes, settings, {})
        with wave.open(io.BytesIO(audio), 'rb') as wav:
            self.assertFalse(any(wav.readframes(wav.getnframes())))
        cancelled = threading.Event()
        cancelled.set()
        self.assertIsNone(render(notes, settings, {'Melody': 'Piano'}, cancelled))


if __name__ == '__main__':
    unittest.main()
