import unittest
from unittest.mock import Mock, patch
import numpy as np
import sounddevice as sd
from audio_output import AudioPlayer


class OutputTests(unittest.TestCase):
    def test_resampling_preserves_audio_after_two_seconds_on_windows(self):
        # At Windows' default int32 width, frame * source_rate overflowed and
        # repeatedly played the first ~2 seconds followed by zeros.
        for source_rate in (22050, 44100):
            with self.subTest(source_rate=source_rate):
                player = AudioPlayer()
                player.volume = 1
                seconds = np.arange(1, 7, dtype=np.float32) / 10
                samples = np.column_stack((np.repeat(seconds, source_rate),) * 2)
                with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 48000, 'max_output_channels': 2}):
                    with patch('audio_output.sd.OutputStream') as factory:
                        player.play_samples(samples, source_rate, 17, loop=True)
                        output = np.zeros((48000 * 6, 2), dtype=np.float32)
                        factory.call_args.kwargs['callback'](output, len(output), None, None)
                        for second, expected in enumerate(seconds):
                            np.testing.assert_allclose(output[second * 48000 + 16:(second + 1) * 48000 - 16], expected)
                        player.stop()

    def test_instrument_refresh_resumes_at_current_position(self):
        player = AudioPlayer()
        player.volume = 1
        samples = np.column_stack((np.arange(1, 9, dtype=np.float32) / 10,) * 2)
        with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 2, 'max_output_channels': 2}):
            with patch('audio_output.sd.OutputStream') as factory:
                player.play_samples(samples, 2, 17, loop=True, start_time=2.5)
                output = np.zeros((2, 2), dtype=np.float32)
                factory.call_args.kwargs['callback'](output, 2, None, None)
                np.testing.assert_allclose(output[:, 0], [.6, .7])
                player.stop()

    def test_all_eight_bars_play_before_wrap_without_export_silence(self):
        player = AudioPlayer()
        player.volume = 1
        # Eight distinguishable bars followed by the export-only tail.
        body = np.repeat(np.arange(1, 9, dtype=np.float32) / 10, 5)
        samples = np.column_stack((np.r_[body, np.zeros(10)],) * 2)
        with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 40, 'max_output_channels': 2}):
            with patch('audio_output.sd.OutputStream') as factory:
                player.play_samples(samples, 40, 17, loop=True, loop_duration=1)
                callback = factory.call_args.kwargs['callback']
                blocks = []
                for _ in range(20):
                    output = np.zeros((7, 2), dtype=np.float32)
                    callback(output, 7, None, None)
                    blocks.append(output.copy())
                played = np.concatenate(blocks)
                expected = np.tile(body, 4)[:len(played)]
                np.testing.assert_allclose(played[:, 0], expected)
                np.testing.assert_allclose(played[:, 1], expected)
                self.assertEqual(player.position, 20)
                player.stop()

    def test_release_tail_carries_across_loop_boundary(self):
        player = AudioPlayer()
        player.volume = 1
        samples = np.column_stack(([.1, .2, .3, .4, .05, .025],) * 2).astype(np.float32)
        with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 4, 'max_output_channels': 2}):
            with patch('audio_output.sd.OutputStream') as factory:
                player.play_samples(samples, 4, 17, loop=True, loop_duration=1)
                output = np.zeros((10, 2), dtype=np.float32)
                factory.call_args.kwargs['callback'](output, 10, None, None)
                np.testing.assert_allclose(output[:, 0], [.15, .225, .3, .4, .15, .225, .3, .4, .15, .225])
                player.stop()

    def test_selected_device_and_volume_reach_output_stream(self):
        player = AudioPlayer()
        player.volume = .5
        samples = np.ones((12, 2), dtype=np.float32) * .4
        with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 44100, 'max_output_channels': 2}):
            with patch('audio_output.sd.OutputStream') as factory:
                player.play_samples(samples, 44100, 17, loop=True)
                self.assertEqual(factory.call_args.kwargs['device'], 17)
                callback = factory.call_args.kwargs['callback']
                output = np.zeros((7, 2), dtype=np.float32)
                callback(output, 7, None, None)
                np.testing.assert_allclose(output, .2)
                callback(output, 7, None, None)
                np.testing.assert_allclose(output, .2)
                self.assertEqual(player.position, 2)
                player.stop()
                factory().close.assert_called_once()

    def test_non_looping_output_finishes_and_zero_fills(self):
        player = AudioPlayer()
        samples = np.ones((3, 2), dtype=np.float32) * .4
        with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 44100, 'max_output_channels': 2}):
            with patch('audio_output.sd.OutputStream') as factory:
                player.play_samples(samples, 44100, 17)
                output = np.ones((7, 2), dtype=np.float32)
                with self.assertRaises(sd.CallbackStop):
                    factory.call_args.kwargs['callback'](output, 7, None, None)
                np.testing.assert_allclose(output[:3], .32)
                np.testing.assert_array_equal(output[3:], 0)
                player.stop()

    def test_cannot_open_device_reports_failure(self):
        player = AudioPlayer()
        with patch('audio_output.sd.query_devices', return_value={'default_samplerate': 44100, 'max_output_channels': 2}):
            with patch('audio_output.sd.OutputStream', side_effect=RuntimeError('Device unavailable')):
                with self.assertRaisesRegex(RuntimeError, 'Device unavailable'):
                    player.play_samples(np.ones((3, 2), dtype=np.float32), 44100, 17)
        self.assertFalse(player.playing)


if __name__ == '__main__':
    unittest.main()
