"""Explicit audio-device playback, isolated from composition and MIDI code."""
import io
import json
from pathlib import Path
import wave
import numpy as np
import sounddevice as sd

PREFERENCES = Path(__file__).with_name('audio_settings.json')


class AudioPlayer:
    def __init__(self):
        self.stream = None
        self.position = 0
        self.loop = False
        self.volume = .8
        self.sample_rate = 1
        self.loop_frames = 0

    @staticmethod
    def devices():
        hosts = sd.query_hostapis()
        return {f"{device['name']} [{hosts[device['hostapi']]['name']}]": index
                for index, device in enumerate(sd.query_devices())
                if device['max_output_channels'] > 0}

    @staticmethod
    def preferred_device(devices):
        try:
            name = json.loads(PREFERENCES.read_text(encoding='utf-8-sig'))['output_name']
            if name in devices:
                return name
        except (OSError, ValueError, KeyError):
            pass
        default = sd.default.device[1]
        return next((name for name, index in devices.items() if index == default), next(iter(devices), ''))

    @staticmethod
    def remember_device(name):
        PREFERENCES.write_text(json.dumps({'output_name': name}, indent=2))

    @property
    def playing(self):
        return self.stream is not None and self.stream.active

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play_wav(self, audio, device, loop=False, loop_duration=None, start_time=0):
        with wave.open(io.BytesIO(audio), 'rb') as wav:
            if wav.getsampwidth() != 2:
                raise ValueError('Expected 16-bit WAV audio')
            samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
            samples = samples.reshape(-1, wav.getnchannels()).astype(np.float32) / 32768
            rate = wav.getframerate()
        self.play_samples(samples, rate, device, loop, loop_duration, start_time)

    def play_samples(self, samples, sample_rate, device, loop=False, loop_duration=None, start_time=0):
        self.stop()
        info = sd.query_devices(device, 'output')
        rate = int(info['default_samplerate'])
        # Rendered WAVs remain portable; adapt to the selected device's native rate.
        if rate != sample_rate:
            length = round(len(samples) * rate / sample_rate)
            # Windows defaults arange to int32. Multiplying frame indices by
            # 22050 overflows after ~2 seconds at 48 kHz and replays the start.
            positions = np.arange(length, dtype=np.float64) * (sample_rate / rate)
            samples = np.column_stack([np.interp(positions, np.arange(len(samples)), samples[:, i])
                                       for i in range(samples.shape[1])]).astype(np.float32)
        if info['max_output_channels'] == 1:
            samples = samples.mean(axis=1, keepdims=True)
        self.sample_rate = rate
        self.loop_frames = len(samples) if loop_duration is None else round(loop_duration * rate)
        if not 0 < self.loop_frames <= len(samples):
            raise ValueError('Loop duration must fall within the audio')
        # Exports include release tails. Loop only the musical bars, carrying
        # each tail into the beginning of the next pass instead of adding a gap.
        loop_samples = samples[:self.loop_frames].copy()
        tail = samples[self.loop_frames:]
        for offset in range(0, len(tail), self.loop_frames):
            chunk = tail[offset:offset + self.loop_frames]
            loop_samples[:len(chunk)] += chunk
        peak = float(np.max(np.abs(loop_samples)))
        if peak > 1:
            loop_samples /= peak
        start_frame = max(0, round(start_time * rate))
        self.position = start_frame % self.loop_frames if loop else min(start_frame, len(samples) - 1)
        self.loop = loop

        def callback(outdata, frames, time_info, status):
            outdata.fill(0)
            written = 0
            while written < frames:
                current = loop_samples if self.loop else samples
                if self.position >= len(current):
                    if self.loop:
                        self.position %= len(current)
                    else:
                        raise sd.CallbackStop
                count = min(frames - written, len(current) - self.position)
                outdata[written:written + count] = current[self.position:self.position + count] * self.volume
                written += count
                self.position += count
                if self.position == len(current):
                    if self.loop:
                        self.position = 0
                    else:
                        raise sd.CallbackStop
        try:
            self.stream = sd.OutputStream(device=device, samplerate=rate,
                                          channels=samples.shape[1], dtype='float32', callback=callback)
            self.stream.start()
        except Exception:
            self.stop()
            raise

    def test_tone(self, device):
        rate = 44100
        t = np.arange(int(rate * .7)) / rate
        envelope = np.minimum(t / .03, 1) * np.minimum((.7 - t) / .06, 1)
        tone = (.18 * np.sin(2 * np.pi * 440 * t) * envelope).astype(np.float32)
        self.play_samples(np.column_stack((tone, tone)), rate, device)
