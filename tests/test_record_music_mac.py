"""Exercise capture-clock measurement and sync across the exported cuts."""
import json
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import wave
from pathlib import Path

import numpy as np

try:
    import record_music_mac as recorder
except ImportError:
    recorder = None


@unittest.skipUnless(recorder and shutil.which('ffmpeg'), 'Requires Playwright and ffmpeg')
class RecordingSyncTests(unittest.TestCase):
    def test_measured_sync_survives_both_export_cuts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / 'video.webm'
            subprocess.run([
                'ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
                'color=black:s=180x320:r=25:d=6', '-vf',
                "drawbox=c=0x00ff00:t=fill:enable='between(t,1,1.39)+between(t,5,5.39)',"
                "drawbox=c=blue:t=fill:enable='between(t,2.8,3.19)'",
                '-c:v', 'libvpx', str(video)
            ], check=True)
            # Test audio that starts both later and earlier than the video.
            for offset in (0.6, -0.3):
                with self.subTest(offset=offset):
                    rate, speed = 48000, 1.004
                    samples = np.zeros(rate * 7)
                    for video_start, frequency in ((1, 997), (5, 997), (2.8, 440)):
                        start = (video_start - offset) * speed
                        a, b = round(start * rate), round((start + .4 * speed) * rate)
                        samples[a:b] = .35 * np.sin(2 * np.pi * frequency * np.arange(b-a) / rate)
                    audio = root / 'audio.wav'
                    with wave.open(str(audio), 'wb') as wav:
                        wav.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
                        wav.writeframes((samples * 32767).astype('<i2').tobytes())
                    measured = recorder.measure_sync(video, audio)
                    self.assertAlmostEqual(measured['offset'], offset, delta=.04)
                    self.assertAlmostEqual(measured['audio_speed'], speed, delta=.006)
                    target = root / 'final.mp4'
                    recorder.export_recording(
                        video, audio, root / 'full.mkv', target,
                        measured['offset'], 2, 4, 1,
                        audio_speed=measured['audio_speed'], intro_min=1.65,
                        video_duration=6
                    )
                    colors = np.frombuffer(subprocess.check_output([
                        'ffmpeg', '-v', 'error', '-i', str(target),
                        '-vf', 'fps=25,scale=1:1', '-pix_fmt', 'rgb24',
                        '-an', '-f', 'rawvideo', '-'
                    ]), dtype=np.uint8).reshape(-1, 3)
                    visual = recorder._runs((colors[:, 2] > 180) & (colors[:, 0] < 40), 3)
                    self.assertEqual(len(visual), 2)
                    audio_out = np.frombuffer(subprocess.check_output([
                        'ffmpeg', '-v', 'error', '-i', str(target),
                        '-vn', '-ac', '1', '-ar', str(rate), '-f', 'f32le', '-'
                    ]), dtype='<f4')
                    size = 480
                    blocks = audio_out[:len(audio_out)//size*size].reshape(-1, size)
                    reference = np.exp(-2j * np.pi * 440 * np.arange(size) / rate)
                    strength = np.abs(blocks @ reference) * 2 / size
                    audible = recorder._runs(strength > .1, 10)
                    self.assertEqual(len(audible), 2)
                    for flash, tone in zip(visual, audible):
                        self.assertAlmostEqual(flash[0]/25, tone[0]/100, delta=.06)
                    self.assertFalse(target.with_name('final.partial.mp4').exists())
                    probe = json.loads(subprocess.check_output([
                        'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(target)
                    ]))
                    streams = probe['streams']
                    self.assertEqual([s['codec_name'] for s in streams], ['h264', 'aac'])
                    self.assertAlmostEqual(float(streams[0]['duration']),
                                           float(streams[1]['duration']), delta=.06)

    def test_missing_markers_fail_instead_of_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / 'video.webm'
            subprocess.run([
                'ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
                'color=black:s=180x320:r=25:d=1', '-c:v', 'libvpx', str(video)
            ], check=True)
            audio = root / 'audio.wav'
            with wave.open(str(audio), 'wb') as wav:
                wav.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(96000))
            with self.assertRaisesRegex(RuntimeError, 'markers missing'):
                recorder.measure_sync(video, audio)


@unittest.skipUnless(recorder, 'Requires Playwright')
class NativeAudioCaptureTests(unittest.TestCase):
    def test_native_buffers_are_written_without_gaps_and_drained_on_stop(self):
        # Arbitrary host buffer sizes, including a final callback during stop.
        chunks = [np.arange(n * 2, dtype='<i2').tobytes() for n in (128, 512, 256, 1024)]
        stream = Mock()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = recorder.BlackHoleRecorder(root/'audio.wav', (0, 44100), root/'audio.log')
            def start():
                for data in chunks[:-1]:
                    capture._callback(data, len(data)//4, None, None)
            stream.start.side_effect = start
            stream.stop.side_effect = lambda: capture._callback(chunks[-1], 1024, None, None)
            with patch('sounddevice.RawInputStream', return_value=stream) as factory:
                with capture:
                    self.assertTrue(capture.ready.is_set())
            self.assertIsNone(capture.error)
            with wave.open(str(root/'audio.wav')) as wav:
                self.assertEqual(wav.getframerate(), 44100)
                self.assertEqual(wav.getnchannels(), 2)
                self.assertEqual(wav.readframes(wav.getnframes()), b''.join(chunks))
            self.assertEqual(factory.call_args.kwargs['blocksize'], 0)
            self.assertEqual(factory.call_args.kwargs['latency'], 'high')
            stream.close.assert_called_once()

    def test_input_overflow_is_reported_instead_of_exporting_a_bad_take(self):
        stream = Mock()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = recorder.BlackHoleRecorder(root/'audio.wav', (0, 48000), root/'audio.log')
            stream.start.side_effect = lambda: capture._callback(bytes(4096), 1024, None, 'input overflow')
            with patch('sounddevice.RawInputStream', return_value=stream):
                with capture:
                    pass
            self.assertIn('lost samples', capture.error)
            self.assertIn('input overflow', (root/'audio.log').read_text())


if __name__ == '__main__':
    unittest.main()
