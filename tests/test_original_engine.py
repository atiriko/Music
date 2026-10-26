"""Regression tests exercise the user's original engine and MIDI scheduler."""
import threading
import unittest
from unittest.mock import Mock, patch
import main
from Event import Event
from Sheduler import Sheduler
from Tempo import Tempo
from generator import Settings, build_scheduler, generate


class OriginalEngineTests(unittest.TestCase):
    def test_requested_length_uses_full_progression(self):
        with patch('main.chordOrder', wraps=main.chordOrder) as order:
            scheduler = build_scheduler(Settings(bars=8, seed=73))
        self.assertEqual(order.call_args.args[0], 8)
        for bar in range(8):
            start = bar * scheduler.tempo.whole
            self.assertTrue(any(event.channel == 1 and abs(event.nominal_time - start) < 1e-8
                                for event in scheduler.queue), f'Missing chords in bar {bar + 1}')
            self.assertTrue(any(event.channel == 0 and start <= event.time < start + scheduler.tempo.whole
                                for event in scheduler.queue), f'Missing melody in bar {bar + 1}')

    def test_original_chord_helpers(self):
        for helper, expected in [(main.majorChord, [60, 64, 67]),
                                 (main.minorChord, [60, 63, 67]),
                                 (main.diminishedChord, [60, 63, 66])]:
            scheduler = Sheduler(Tempo(120), None)
            helper(60, 1, 1, scheduler, 0, 0, 1)
            self.assertEqual([event.note for event in scheduler.queue], expected)

    def test_gui_uses_original_composition_functions(self):
        with patch('main.generateChortProgression', wraps=main.generateChortProgression) as chords:
            with patch('main.generateMelody', wraps=main.generateMelody) as melody:
                generate(Settings(bars=1))
        chords.assert_called_once()
        melody.assert_called_once()

    def test_original_chord_transition_rules(self):
        transitions = {0: set(range(7)), 1: {4, 6}, 2: {5}, 3: {4, 6}, 4: {0}, 5: {1, 3}, 6: {0, 4}}
        for _ in range(10):
            progression = main.chordOrder(20)
            for before, after in zip(progression, progression[1:]):
                self.assertIn(after, transitions[before])

    def test_scheduler_keeps_off_grid_notes_and_note_offs(self):
        output = Mock()
        scheduler = Sheduler(Tempo(120), output)
        scheduler.addEvent(Event(1, 60, .001, .006))
        scheduler.addEvent(Event(1, 62, .007, .003))
        scheduler.play(threading.Event())
        self.assertEqual([call.args[0] for call in output.send_message.call_args_list],
                         [[0x91, 60, 112], [0x81, 60, 0], [0x91, 62, 112], [0x81, 62, 0]])
        self.assertEqual(len(scheduler.queue), 2)

    def test_stop_releases_sounding_notes(self):
        output = Mock()
        stop = Mock()
        stop.wait.side_effect = [False, True]
        scheduler = Sheduler(Tempo(120), output)
        scheduler.addEvent(Event(0, 60, 0, 100))
        scheduler.play(stop)
        self.assertEqual([call.args[0] for call in output.send_message.call_args_list],
                         [[0x90, 60, 112], [0x80, 60, 0]])

    def test_overlapping_notes_release_after_last_event(self):
        output = Mock()
        scheduler = Sheduler(Tempo(120), output)
        scheduler.addEvent(Event(0, 60, 0, .01))
        scheduler.addEvent(Event(0, 60, .003, .02))
        scheduler.play(threading.Event())
        self.assertEqual([call.args[0][0] for call in output.send_message.call_args_list], [0x90, 0x90, 0x80])
        self.assertAlmostEqual(scheduler.time, .023)

    def test_original_save_format(self):
        scheduler = build_scheduler(Settings(bars=1))
        with patch('builtins.open', unittest.mock.mock_open()) as output:
            scheduler.save()
        lines = [call.args[0].split() for call in output().write.call_args_list]
        self.assertEqual(len(lines), len(scheduler.queue))
        self.assertTrue(all(len(line) == 5 for line in lines))

    def test_event_bar_number(self):
        event = Event(0, 60, 3, 1)
        self.assertEqual(event.setBar(Tempo(120, 3, 4)), 2)


if __name__ == '__main__':
    unittest.main()
