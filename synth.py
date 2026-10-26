"""Render the original engine's notes using a bundled sampled SoundFont.

TinySoundFont renders in-process. Audio device playback stays in audio_output;
no external MIDI ports, running synth applications, or plugins are required.
"""
import io
from pathlib import Path
import wave
import numpy as np
import tinysoundfont
from Instruments import SOUNDFONT_PROGRAMS, DRUM_KITS
from mix_settings import controllers
from soundbanks import voice as resolve_voice
from production import finish

SAMPLE_RATE = 22050
SOUNDFONT = Path(__file__).parent / 'assets' / 'soundfonts' / 'GeneralUser-GS.sf2'
INSTRUMENTS = tuple(SOUNDFONT_PROGRAMS)
CHANNELS = {'Melody': 0, 'Chords': 1, 'Bass': 2, 'Drums': 9}


def render(notes, settings, instruments, cancelled=None, master=True, _stem=False):
    """Return stereo 16-bit WAV bytes; None instruments mute their part."""
    if any(voice is not None and voice not in (DRUM_KITS if part == 'Drums' else SOUNDFONT_PROGRAMS)
           for part, voice in instruments.items()):
        raise ValueError('Unknown instrument')
    if cancelled is not None and cancelled.is_set():
        return None
    if not _stem:
        from production import mix_stems
        stems = {}
        for part, selected_voice in instruments.items():
            if selected_voice is not None:
                stem = render(notes, settings, {part: selected_voice}, cancelled, _stem=True)
                if stem is None:
                    return None
                stems[part] = stem
        frames = int((settings.bars * 4 * 60 / settings.bpm + 1) * SAMPLE_RATE)
        mix = mix_stems(stems, notes, settings, SAMPLE_RATE) if stems else np.zeros((frames, 2), dtype=np.float32)
        if master:
            mix = finish(mix, SAMPLE_RATE, settings.mix_profile)
        return encode(mix)
    seconds_per_beat = 60 / settings.bpm
    frames = int((settings.bars * 4 * seconds_per_beat + 1) * SAMPLE_RATE)
    mix = np.zeros((frames, 2), dtype=np.float32)
    selected = {part: voice for part, voice in instruments.items() if voice is not None}
    if selected:
        if not SOUNDFONT.is_file():
            raise FileNotFoundError(f'Missing bundled instrument library: {SOUNDFONT}')
        synth = tinysoundfont.Synth(samplerate=SAMPLE_RATE, gain=-3)
        loaded = {}
        descriptors = {part: resolve_voice(voice, part == 'Drums') for part, voice in selected.items()}
        for descriptor in descriptors.values():
            path = descriptor['file']
            if not Path(path).is_file():
                raise FileNotFoundError('Missing instrument library: ' + path)
            if path not in loaded:
                loaded[path] = synth.sfload(path)
        try:
            for part, voice in selected.items():
                channel = CHANNELS[part]
                drums = part == 'Drums'
                descriptor = descriptors[part]
                synth.program_select(channel, loaded[descriptor['file']], descriptor['bank'], descriptor['program'], is_drums=drums)
                for control, value in controllers(part, settings.mix_profile).items():
                    synth.control_change(channel, control, value)
            timeline = []
            for note in notes:
                if note.part not in selected:
                    continue
                channel = CHANNELS[note.part]
                start = round(note.beat * seconds_per_beat * SAMPLE_RATE)
                end = round((note.beat + note.duration) * seconds_per_beat * SAMPLE_RATE)
                velocity = max(1, min(127, round(note.velocity * 127)))
                timeline.append((start, 1, channel, note.pitch, velocity))
                timeline.append((end, 0, channel, note.pitch, 0))
            timeline.sort()
            position = 0
            active = {}

            def fill(end):
                nonlocal position
                while position < end:
                    if cancelled is not None and cancelled.is_set():
                        return False
                    count = min(2048, end - position)
                    block = np.frombuffer(synth.generate(count), dtype=np.float32).reshape(-1, 2)
                    mix[position:position + count] = block
                    position += count
                return True

            for frame, is_on, channel, pitch, velocity in timeline:
                if not fill(min(frame, frames)):
                    return None
                key = (channel, pitch)
                if is_on:
                    synth.noteon(channel, pitch, velocity)
                    active[key] = active.get(key, 0) + 1
                elif key in active:
                    active[key] -= 1
                    if active[key] == 0:
                        synth.noteoff(channel, pitch)
                        del active[key]
            if not fill(frames):
                return None
        finally:
            for font_id in loaded.values():
                synth.sfunload(font_id)
    return mix


def encode(mix):
    frames = len(mix)
    # Fade the end of the export tail rather than cutting a ringing sample.
    fade = min(round(.05 * SAMPLE_RATE), frames)
    mix[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
    mix[-100:] = 0
    peak = float(np.max(np.abs(mix)))
    if peak > .95:
        mix *= .95 / peak
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes((mix * 32767).astype('<i2').tobytes())
    return output.getvalue()
