"""Octave placement must vary without changing the underlying composition."""
import unittest
from generator import Note, Settings, generate
from Instruments import SOUNDFONT_PROGRAMS
from registers import arrange, comfort_zone
from song import Song, Section, compile_song


class RegisterTests(unittest.TestCase):
    def test_seed_varies_each_role_by_whole_phrase_octaves(self):
        notes = [Note(part, pitch, beat, .8, .7)
                 for part, pitches in [('Melody', (72, 74, 76)),
                                       ('Chords', (55, 60, 64)), ('Bass', (36, 40, 43))]
                 for beat, pitch in enumerate(pitches)]
        for part in ('Melody', 'Chords', 'Bass'):
            signatures = set()
            for seed in range(16):
                placed = arrange(notes, seed)
                shifts = {b.pitch - a.pitch for a, b in zip(notes, placed) if a.part == part}
                self.assertEqual(len(shifts), 1)
                self.assertTrue(all(shift % 12 == 0 for shift in shifts))
                signatures.add(tuple(n.pitch for n in placed if n.part == part))
            self.assertGreater(len(signatures), 1, part)

    def test_every_instrument_respects_its_zone_and_preserves_music(self):
        settings = Settings(seed=17, complexity='Intricate', bars=8)
        baseline = generate(settings)
        for instrument in SOUNDFONT_PROGRAMS:
            instruments = dict.fromkeys(('Melody', 'Chords', 'Bass'), instrument)
            notes = generate(settings, instruments)
            with self.subTest(instrument=instrument):
                self.assertEqual(notes, generate(settings, instruments))
                self.assertEqual(len(baseline), len(notes))
                for before, after in zip(baseline, notes):
                    # Instrument-specific articulation (strums, legato, pedal)
                    # may nudge timing slightly, but never rewrites the music.
                    self.assertEqual(before.part, after.part)
                    self.assertLess(abs(before.beat - after.beat), .1)
                    if after.part == 'Drums':
                        self.assertEqual(before, after)
                    else:
                        low, high, _ = comfort_zone(after.part, instrument)
                        self.assertTrue(low <= after.pitch <= high)
                        self.assertEqual(before.pitch % 12, after.pitch % 12)

    def test_song_uses_instrument_ranges_and_repeats_stay_identical(self):
        settings = Settings(seed=5)
        sections = {name: Section(name, settings, {'Melody': instrument})
                    for name, instrument in [('High', 'Piccolo'), ('Low', 'Cello')]}
        clips = compile_song(Song(110, sections, ['High', 'Low', 'High']))
        average = lambda clip: sum(n.pitch for n in clip.notes if n.part == 'Melody') / sum(n.part == 'Melody' for n in clip.notes)
        self.assertGreater(average(clips[0]), average(clips[1]) + 12)
        self.assertEqual(clips[0].notes, clips[2].notes)

    def test_humanized_downbeat_uses_score_phrase_not_early_playback_time(self):
        notes = [Note('Melody', 72, 15.98, .8, .7), Note('Melody', 76, 16.5, .4, .6)]
        placed = arrange(notes, 2, score_beats=[16, 16.5])
        self.assertEqual(placed[1].pitch - placed[0].pitch, 4)


if __name__ == '__main__':
    unittest.main()
