"""Standard MIDI export of generator clips and complete song arrangements."""
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from Instruments import SOUNDFONT_PROGRAMS, DRUM_KITS
from mix_settings import controllers
from soundbanks import voice as resolve_voice

CHANNELS = {'Melody': 0, 'Chords': 1, 'Bass': 2, 'Countermelody': 3, 'Drums': 9}


def save_midi(path, notes, settings, instruments):
    save_midi_clips(path, [(0, notes, instruments, settings.mix_profile)], settings.bpm, settings.bars * 4)


def save_midi_clips(path, clips, bpm, total_beats):
    """Clips are (start beat, notes relative to clip, instruments) tuples."""
    midi = MidiFile(type=1, ticks_per_beat=480)
    end_tick = round(total_beats * midi.ticks_per_beat)
    tempo = MidiTrack()
    midi.tracks.append(tempo)
    tempo.extend([MetaMessage('track_name', name='Tempo'),
                  MetaMessage('set_tempo', tempo=bpm2tempo(bpm)),
                  MetaMessage('time_signature', numerator=4, denominator=4),
                  MetaMessage('end_of_track', time=end_tick)])
    for part, channel in CHANNELS.items():
        events = []
        first_voice = None
        for clip in clips:
            offset, notes, instruments = clip[:3]
            profile = clip[3] if len(clip) > 3 else 'Balanced'
            voice = instruments.get(part)
            if voice is None:
                continue
            first_voice = first_voice or voice
            descriptor = resolve_voice(voice, part == 'Drums')
            program = descriptor['program']
            tick = round(offset * 480)
            events.append((tick, 1, 0, descriptor['bank'] & 127))
            events.append((tick, 1, 32, 0))
            for control, value in controllers(part, profile).items():
                events.append((tick, 1, control, value))
            events.append((tick, 2, program, 0))
            for note in notes:
                if note.part != part:
                    continue
                start = round((offset + note.beat) * 480)
                end = max(start + 1, round((offset + note.beat + note.duration) * 480))
                events.append((start, 3, note.pitch, max(1, min(127, round(note.velocity * 127)))))
                events.append((end, 0, note.pitch, 0))
        if first_voice is None or not any(event[1] == 3 for event in events):
            continue
        track = MidiTrack()
        midi.tracks.append(track)
        track.append(MetaMessage('track_name', name=part + ' - ' + first_voice))
        previous = 0
        for tick, kind, value, velocity in sorted(events):
            if kind == 1:
                message = Message('control_change', channel=channel, control=value, value=velocity, time=tick - previous)
            elif kind == 2:
                message = Message('program_change', channel=channel, program=value, time=tick - previous)
            else:
                message = Message('note_on' if kind == 3 else 'note_off', channel=channel,
                                  note=value, velocity=velocity, time=tick - previous)
            track.append(message)
            previous = tick
        track.append(MetaMessage('end_of_track', time=max(0, end_tick - previous)))
    midi.save(path)
