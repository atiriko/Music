"""Musical and performance regressions shared by desktop and mobile."""
from dataclasses import replace
import unittest
import numpy as np
from generator import Settings, generate, build_scheduler, SCALES
from accompaniment import CHORD_STYLES, BASS_STYLES
from production import finish


class AccompanimentTests(unittest.TestCase):
    def test_variations_change_harmony_and_bass_beyond_velocity(self):
        for bars in (2, 8):
            signatures = {part: set() for part in ('Chords', 'Bass')}
            harmonies = set()
            for seed in range(12):
                scheduler = build_scheduler(Settings(bars=bars, seed=seed, feel='Tight'))
                harmonies.add(tuple((start, root) for start, _, root, _ in scheduler.harmony))
                for part, channel in (('Chords', 1), ('Bass', 2)):
                    signatures[part].add(tuple((e.note, e.time, e.length) for e in sorted(scheduler.queue) if e.channel == channel))
            self.assertGreater(len(harmonies), 3)
            for values in signatures.values():
                self.assertGreater(len(values), 8)

    def test_every_pattern_is_diatonic_and_bass_anchors_each_change(self):
        for scale, offsets in SCALES.items():
            for chord in CHORD_STYLES:
                for bass in BASS_STYLES:
                    scheduler = build_scheduler(Settings(scale=scale, bars=4, complexity='Intricate',
                                                         chord_style=chord, bass_style=bass))
                    for start, _, root, tones in scheduler.harmony:
                        anchors = [e for e in scheduler.queue if e.channel == 2 and
                                   abs(e.nominal_time / scheduler.tempo.quarter - start) < 1e-8]
                        expected = sorted({p % 12 for p in offsets})[root]
                        self.assertTrue(anchors)
                        self.assertEqual(anchors[0].note % 12, expected)
                        self.assertTrue(all(p % 12 in offsets for p in tones))

    def test_feel_changes_timing_without_changing_the_score(self):
        settings = Settings(seed=17)
        tight = build_scheduler(replace(settings, feel='Tight'))
        natural = build_scheduler(settings)
        score = lambda scheduler: [(e.channel, e.note, e.nominal_time, e.nominal_length) for e in scheduler.queue]
        self.assertEqual(score(tight), score(natural))
        self.assertTrue(any(a.time != b.time for a, b in zip(tight.queue, natural.queue)))
        self.assertTrue(all(abs(e.time - e.nominal_time) < .04 for e in natural.queue))
        self.assertEqual(generate(settings), generate(settings))

    def test_room_has_a_decay_and_no_clipping_or_nonfinite_samples(self):
        audio = np.zeros((22050, 2), dtype=np.float32)
        audio[0] = 4
        output = finish(audio, 22050)
        self.assertTrue(np.all(np.isfinite(output)))
        self.assertLessEqual(float(np.abs(output).max()), .95)
        self.assertGreater(float(np.abs(output[400:8000]).sum()), .01)
        self.assertFalse(np.array_equal(output[:, 0], output[:, 1]))


if __name__ == '__main__':
    unittest.main()
