import time
import random
import Notes
import numpy as np
import threading
import Tempo
import Sheduler
import Event
import Instruments
import ProgressionStateMachine as PSM
#scales
majorScale = [0, 2, 4, 5, 7, 9, 11, 12]
minorScale = [0, 2, 3, 5, 7, 8, 10, 12]
pentatonicScale = [0, 3, 5, 7, 10, 12, 15, 17]
dorianScale = [0, 2, 3, 5, 7, 9, 10, 12]
phrygianScale = [0, 1, 3, 5, 7, 8, 10, 12]
lydianScale = [0, 2, 4, 6, 7, 9, 11, 12]
mixolydianScale = [0, 2, 4, 5, 7, 9, 10, 12]
locrianScale = [0, 1, 3, 5, 6, 8, 10, 12]
harmonicMinorScale = [0, 2, 3, 5, 7, 8, 11, 12]
harmonicMajorScale = [0, 2, 4, 5, 7, 8, 11, 12]
melodicMinorScale = [0, 2, 3, 5, 7, 9, 11, 12]
melodicMajorScale = [0, 2, 4, 5, 7, 9, 11, 12]
bluesScale = [0, 3, 5, 6, 7, 10, 12, 15]
wholeToneScale = [0, 2, 4, 6, 8, 10, 12]
jazzMinorScale = [0, 1, 3, 4, 7, 9, 10, 12]
jazzMajorScale = [0, 2, 4, 5, 7, 9, 11, 12]
bebopScale = [0, 2, 4, 5, 7, 9, 10, 11, 12]
Tempo = Tempo.Tempo

 
def scaleNote(key, scale, degree):
    """Convert a scale degree to MIDI pitch, including octave crossings."""
    scale = sorted({offset % 12 for offset in scale})
    octave, index = divmod(degree, len(scale))
    return key + scale[index] + 12 * octave


def majorChord(note, delay,channel,scheduler,bar, index,numberOfChords):
    time = delay*bar*numberOfChords + delay*index
    # for i in range(0, 3):
    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))

def minorChord(note, delay,channel,scheduler,bar, index,numberOfChords):
    time = delay*bar*numberOfChords + delay*index

    
    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))

def diminishedChord(note, delay, channel,scheduler,bar, index,numberOfChords):
    time = delay*bar*numberOfChords + delay*index

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time, length=delay))



def generateMelody(key, midiout, tempo, scale, channel, length,
                   scheduler=None, complexity=1, rng=None, phrasing='Balanced'):
    """Develop a two-bar motif over the scheduled harmony.

    Strong beats use chord tones, weak beats mostly move by scale step,
    larger movements recover in the opposite direction, and phrases resolve.
    """
    rng = rng if rng is not None else np.random.default_rng()
    scale = sorted({offset % 12 for offset in scale})
    rhythms = ((1, 2), (.5, 1, 1), (.25, .5, .5, 1))[complexity]
    motifs = []
    for motif_index in range(2):
        pattern = []
        beat = 0
        while beat < 4:
            # Never skip the harmonic anchors at beats one and three.
            boundary = 2 if beat < 2 else 4
            duration = min(float(rng.choice(rhythms)), boundary - beat)
            pattern.append((beat, duration))
            beat += duration
        if phrasing != 'Continuous':
            cutoff = 3 if phrasing == 'Spacious' else (3.5 if motif_index == 1 else 4)
            rest_probability = .35 if phrasing == 'Spacious' else .18
            pattern = [(beat, min(duration, cutoff - beat)) for beat, duration in pattern
                       if beat < cutoff and (beat in (0, 2) or rng.random() >= rest_probability)]
        motifs.append(pattern)
    contours = ((1, 1, -1, -1, 1, 0, -1, 0), (0, 1, -1, 1, 1, -1, -1, 0),
                (-1, -1, 1, 1, 0, 1, -1, 0))
    contour = contours[int(rng.integers(len(contours)))]
    position = len(scale)
    last_move = 0
    events = []
    bars = int(np.ceil(length / tempo.whole))
    for bar in range(bars):
        start = bar * tempo.whole
        chord_pitches = {event.note % 12 for event in scheduler.queue
                         if event.channel == 1 and abs(event.time - start) < 1e-7} if scheduler else set()
        if not chord_pitches:
            chord_pitches = {scaleNote(key, scale, degree) % 12 for degree in (0, 2, 4)}
        pattern = motifs[bar % 2]
        if bar == bars - 1 and phrasing != 'Continuous':
            cutoff = 3 if phrasing == 'Spacious' else 3.5
            pattern = [(beat, min(beats, cutoff - beat)) for beat, beats in pattern if beat < cutoff]
        for index, (beat, beats) in enumerate(pattern):
            if scheduler is not None and hasattr(scheduler, 'harmony'):
                absolute = bar * 4 + beat
                chord_pitches = next(({p % 12 for p in tones}
                                      for onset, span, _, tones in scheduler.harmony
                                      if onset <= absolute < onset + span), chord_pitches)
            elapsed = start + beat * tempo.quarter
            if elapsed >= length - 1e-9:
                break
            duration = min(beats * tempo.quarter, length - elapsed)
            step = contour[index % len(contour)]
            if abs(last_move) > 1:
                step = -1 if last_move > 0 else 1
            target = max(len(scale) - 3, min(2 * len(scale) - 1, position + step))
            strong = beat in (0, 2)
            if strong:
                candidates = [degree for degree in range(len(scale) - 3, 2 * len(scale))
                              if scaleNote(key, scale, degree) % 12 in chord_pitches]
                chosen = min(candidates, key=lambda degree: (abs(degree - target), abs(degree - position)))
            else:
                chosen = target
            last_in_bar = index == len(pattern) - 1
            if last_in_bar and bar == bars - 1:
                chosen = len(scale)
            elif last_in_bar and (bar + 1) % 4 == 0:
                candidates = [degree for degree in range(len(scale) - 3, 2 * len(scale))
                              if scaleNote(key, scale, degree) % 12 in chord_pitches]
                chosen = min(candidates, key=lambda degree: abs(degree - position))
            last_move = chosen - position
            position = chosen
            velocity = int(rng.integers(88, 106) if strong else rng.integers(70, 90))
            event = Event.Event(channel, scaleNote(key, scale, position), elapsed, duration * .9, velocity)
            events.append(event)
            if scheduler is not None:
                scheduler.addEvent(event)
    return events
    # for i in range(0, 4):
    #     noise_val = noise([i/1000]) *1000
    #     print(noise_val)
    #     delay = tempo.lenghts[random.choice(tempo.tempo2)]
    #     print(key + scale[int(noise_val) % len(scale)])
    #     note = key + scale[int(noise_val) % len(scale)]
    #     note = note - 12
    #     notes.append(note)
    #     delays.append(delay)
    #     # note = key + random.choice(scale)

    #     midiout.send_message([0x90+channel, note, 112])
    #     time.sleep(delay)
    #     midiout.send_message([0x80+channel, note, 0])
    # for i in range(0, 4):
    #         midiout.send_message([0x90+channel, notes[i], 112])
    #         time.sleep(delays[i])
    #         midiout.send_message([0x80+channel, notes[i], 0])

        # generateMelody(notes.E2, midiout, tempo, bluesScale)
def chordOrder(numberOfChords, rng=None):
        rng = rng if rng is not None else np.random.default_rng()
        def nextChord(prevChord):
            if prevChord == 0:
                return rng.choice([0,1,2,3,4,5,6])
            elif prevChord == 1:
                return rng.choice([4,6])
            elif prevChord == 2:
                return 5
            elif prevChord == 3:
                return rng.choice([4,6])
            elif prevChord == 4:
                return 0
            elif prevChord == 5:
                return rng.choice([1,3])
            elif prevChord == 6:
                return rng.choice([0,4])
        firstChord = rng.choice([0,1,2,3,4,5,6],p=[0.76,0.04,0.04,0.04,0.04,0.04,0.04])
        # ,[0.76,0.04,0.04,0.04,0.04,0.04,0.04]
        prevChord = firstChord
        chords = [firstChord]
        for i in range(numberOfChords-1):
            prevChord = nextChord(prevChord)
            chords.append(prevChord)
        return chords
            
        
def pickNextCord(prevnote, notes, scale, key, tempo, channel, scheduler,
                 bar, index, numberOfChords, order=-1, voices=3):
    """Build the chord from this scale instead of assuming major-key qualities.

    Legacy arguments remain accepted. One chord lasts one 4/4 bar.
    """
    scale = sorted({offset % 12 for offset in scale})
    if order == -1:
        order = scale.index((prevnote - key) % 12)
    start = tempo.whole * (bar * numberOfChords + index)
    for offset in range(0, voices * 2, 2):
        pitch = scaleNote(key, scale, order + offset)
        scheduler.addEvent(Event.Event(channel, pitch, start, tempo.whole * .95, 72))

    # return (prevnote+jump,order)

def selectStartingNote():
    noteslist = [i for i in range(24, 92)]
    # Calculate the center index
    center_index = 62

    # Create a quadratic function that decreases from left to right
    def quadratic_function(x):
        return -(x - center_index)**2 / (len(noteslist) / 24)**2

    # Generate x-values for the quadratic function
    x_values = np.arange(len(noteslist))

    # Apply the quadratic function to generate probabilities
    probabilities = quadratic_function(x_values)

    # Normalize the probabilities
    normalized_probabilities = probabilities / np.sum(probabilities)
    return np.random.choice(noteslist,p=normalized_probabilities)
def metronome(sheduler):
    for i in range(0, sheduler.tempo.bpm*3):
        for j in range(0, 4):
            if j == 0:
                note = 51
            else:
                note = 50
            event = Event.Event(channel=0, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
            sheduler.addEvent(event)
def generateChortProgression(key, scale, notes, sheduler, bars=8, complexity=1, rng=None,
                            chord_style='Varied', bass_style='Varied'):
    """Extend the original progression with voiced accompaniment and bass motifs."""
    from accompaniment import generate
    rng = rng if rng is not None else np.random.default_rng()
    scale = sorted({offset % 12 for offset in scale})
    progression = chordOrder(bars, rng)
    generate(key, scale, sheduler, progression, complexity, rng, scaleNote,
             chord_style, bass_style)


def generateDrums(sheduler, bars=8, complexity=1, rng=None, style='Rock', fill_every=4):
    """Keep the original scheduling API; generate a seeded stylistic groove."""
    from drum_patterns import generate
    generate(sheduler, bars, complexity, rng, style, fill_every)


def startScheduler(sheduler,stop_event):

    notes = Notes.Notes()
    scale = minorScale
    key = selectStartingNote()
    generateChortProgression(key, scale, notes, sheduler)
    generateDrums(sheduler)



    # metronome(sheduler)
    sheduler.play(stop_event=stop_event)
def setInstruments(midiout):
        midiout.send_message([0xC9, 0])
        midiout.send_message([0xC0, 0])
        midiout.send_message([0xC1, 48])
        midiout.send_message([0xC5, 60])
        midiout.send_message([0xC3, 117])
        midiout.send_message([0xC2, 33])

        # midiout.send_message([0xC0, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC1, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC5, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC3, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC2, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
def midi_main():
    import rtmidi
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    midiout
    # print(available_ports)
    if available_ports:
        midiout.open_port(0)

        stop_event = threading.Event()
        sheduler = Sheduler.Sheduler(Tempo(120), midiout)
        setInstruments(midiout)

        worker = threading.Thread(target=startScheduler, args=(sheduler,stop_event))
        worker.start()

        try:
            while True:
                entry = input('Press r to restart, s to save, ctrl+c to stop.\n')
                if entry == 'r':
                    stop_event.set()
                    worker.join()
                    stop_event = threading.Event()
                    sheduler = Sheduler.Sheduler(Tempo(120), midiout)

                    worker = threading.Thread(target=startScheduler, args=(sheduler,stop_event))
                    worker.start()
                elif entry == 's':
                    sheduler.save()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            stop_event.set()
            worker.join()
            midiout.close_port()

            

    else:
        print('No MIDI ports available')
    del midiout

def main():
    import sys
    if '--midi' in sys.argv:
        midi_main()
    else:
        from music_app import main as desktop_main
        desktop_main()


if __name__ == '__main__':
    main()
