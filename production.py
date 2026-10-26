"""Small stereo room and gentle tone shaping for the desktop sample renderer.

TinySoundFont has no effects engine. A deterministic sparse room response
supplies early reflections and a filtered decay, with no extra dependencies.
This runs once per render, outside the real-time audio callback.
"""
import numpy as np


def mix_stems(stems, notes, settings, sample_rate):
    """Balance stems, carve space, and duck bass/chords around lead attacks."""
    size = len(next(iter(stems.values())))
    mix = np.zeros((size, 2), dtype=np.float32)
    targets = {'Melody': .075, 'Countermelody': .045, 'Chords': .045, 'Bass': .065, 'Drums': .06}
    for part, audio in stems.items():
        fft_size = 1 << size.bit_length()
        frequencies = np.fft.rfftfreq(fft_size, 1 / sample_rate)
        cutoff = {'Melody': 95, 'Countermelody': 130, 'Chords': 150, 'Bass': 28, 'Drums': 30}[part]
        response = frequencies ** 2 / (frequencies ** 2 + cutoff ** 2)
        if part == 'Chords':
            response *= 1 - .23 * np.exp(-((frequencies - 1600) / 1100) ** 2)
        for channel in range(2):
            audio[:, channel] = np.fft.irfft(np.fft.rfft(audio[:, channel], fft_size) * response, fft_size)[:size]
        rms = float(np.sqrt(np.mean(audio ** 2)))
        gain = min(1.5, max(.65, targets[part] / max(rms, .00001)))
        if part in ('Chords', 'Bass'):
            driver = 'Melody' if part == 'Chords' else 'Drums'
            duck = np.ones(size, dtype=np.float32)
            for note in notes:
                if note.part != driver or (driver == 'Drums' and note.pitch != 36):
                    continue
                start = max(0, round(note.beat * 60 / settings.bpm * sample_rate))
                length = min(round(sample_rate * (.16 if driver == 'Melody' else .12)), size - start)
                if length > 0:
                    curve = 1 - .16 * np.exp(-np.arange(length) / (sample_rate * .045))
                    duck[start:start + length] = np.minimum(duck[start:start + length], curve)
            audio *= duck[:, None]
        mix += audio * gain
    return mix


def finish(mix, sample_rate, profile='Balanced'):
    if not np.any(mix):
        return mix
    count = len(mix)
    tail = int(sample_rate * .42)
    size = 1 << (count + tail - 1).bit_length()
    frequencies = np.fft.rfftfreq(size, 1 / sample_rate)
    # Remove subsonic energy; tame the brittle upper edge of small GM samples.
    tone = (frequencies / np.maximum(frequencies, 28)) ** 2
    tone *= 1 - (.32 if profile == 'Warm' else .16) * frequencies ** 2 / (frequencies ** 2 + 4200 ** 2)
    wet_filter = frequencies ** 2 / (frequencies ** 2 + 240 ** 2)
    wet_filter /= np.sqrt(1 + (frequencies / 3100) ** 4)
    result = np.empty_like(mix)
    for channel in range(2):
        impulse = np.zeros(tail)
        for reflection in range(26):
            seconds = .019 + reflection * .0137 + channel * .0031
            impulse[round(seconds * sample_rate)] += .045 * np.exp(-seconds / .14) * (-1 if reflection % 3 == 0 else 1)
        spectrum = np.fft.rfft(mix[:, channel], size)
        room = np.fft.rfft(impulse, size)
        space = {'Dry': 0, 'Punchy': .6, 'Spacious': 1.8}.get(profile, 1)
        result[:, channel] = np.fft.irfft(spectrum * tone * (1 + space * room * wet_filter), size)[:count]
    # A slow RMS detector controls the bus instead of clipping every transient.
    block = 512
    padded = np.pad(np.mean(result ** 2, axis=1), (0, (-count) % block))
    envelope = np.sqrt(padded.reshape(-1, block).mean(axis=1) + 1e-12)
    envelope = np.convolve(np.pad(envelope, (1, 1), mode='edge'), np.ones(3) / 3, mode='valid')
    reduction = np.minimum(1, (.15 / np.maximum(envelope, .00001)) ** .35)
    result *= np.interp(np.arange(count), np.arange(len(reduction)) * block, reduction)[:, None]
    rms = float(np.sqrt(np.mean(result ** 2)))
    if rms > .00001:
        # Aim for a finished, streaming-ready level (roughly -16 dBFS RMS).
        result *= min(1.8, max(.7, .15 / rms))
    # Smooth peak rounding preserves transients without hard digital clipping.
    return (.95 * np.tanh(result / .95)).astype(np.float32)
