"""Rests must be present in the score and survive export, not just lower volume."""
import tempfile
from pathlib import Path
import unittest
from mido import MidiFile
from generator import Settings, generate, COMPLEXITIES
from midi_export import save_midi


class PhrasingTests(unittest.TestCase):
    def test_ensemble_rests_at_phrase_and_section_endings(self):
        for bars in (1, 2, 4, 5, 8):
            for phrasing, gap in [('Balanced', .5), ('Spacious', 1)]:
                for feel in ('Tight', 'Natural', 'Loose'):
                    notes = generate(Settings(bars=bars, phrasing=phrasing, feel=feel))
                    for end in set(range(16, bars * 4 + 1, 16)) | {bars * 4}:
                        start = end - gap
                        self.assertFalse(any(n.beat < end - 1e-8 and n.beat + n.duration > start + 1e-8 for n in notes),
                                         (bars, phrasing, feel, end))

    def test_melody_has_internal_breaths_and_still_resolves(self):
        for complexity in COMPLEXITIES:
            for bars in (1, 2, 5, 8):
                for seed in range(8):
                    notes = [n for n in generate(Settings(bars=bars, seed=seed, complexity=complexity, feel='Tight'))
                             if n.part == 'Melody']
                    self.assertEqual(notes[-1].pitch % 12, 0)
                    self.assertLessEqual(notes[-1].beat + notes[-1].duration, bars * 4 - .5)
                    if bars >= 4:
                        self.assertTrue(any(b.beat - a.beat - a.duration >= .45 for a, b in zip(notes, notes[1:])))

    def test_density_controls_create_real_changes_in_activity(self):
        counts = []
        for phrasing in ('Continuous', 'Balanced', 'Spacious'):
            counts.append(sum(len(generate(Settings(seed=seed, phrasing=phrasing))) for seed in range(10)))
        self.assertGreater(counts[0], counts[1])
        self.assertGreater(counts[1], counts[2])

    def test_export_has_no_sounding_midi_notes_during_ensemble_break(self):
        settings = Settings(bars=4, feel='Tight')
        instruments = {'Melody': 'Piano', 'Chords': 'Strings', 'Bass': 'Synth bass', 'Drums': 'Standard kit'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'rests.mid'
            save_midi(path, generate(settings, instruments), settings, instruments)
            midi = MidiFile(path)
        for track in midi.tracks:
            tick, active = 0, set()
            for message in track:
                tick += message.time
                if message.type == 'note_on' and message.velocity:
                    self.assertLess(tick, 15.5 * 480)
                    active.add(message.note)
                elif message.type in ('note_off', 'note_on'):
                    self.assertLessEqual(tick, 15.5 * 480)
                    active.discard(message.note)
            self.assertFalse(active)


if __name__ == '__main__':
    unittest.main()
