import time
import rtmidi
import random
import rtmidi.midiutil
import Notes
import threading
import Tempo
import Sheduler
import Event
import sys
import pygameui
import sf2_loader as sf
import ProgressionStateMachine as PSM
import numpy as np
from perlin_noise import PerlinNoise
from PySide6 import QtWidgets


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

 
def majorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))

def minorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))

def diminishedChord(note, delay, channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time, length=delay))


def chordOrder(numberOfChords):
        def nextChord(prevChord):
            if prevChord == 0:
                return np.random.choice([0,1,2,3,4,5,6])
            elif prevChord == 1:
                return np.random.choice([4,6]) 
            elif prevChord == 2:
                return 5
            elif prevChord == 3:
                return np.random.choice([4,6]) 
            elif prevChord == 4:
                return 0
            elif prevChord == 5:
                return np.random.choice([1,3])
            elif prevChord == 6:
                return np.random.choice([0,4])
        firstChord = np.random.choice([0,1,2,3,4,5,6],p=[0.76,0.04,0.04,0.04,0.04,0.04,0.04])
        prevChord = firstChord
        chords = [firstChord]
        for _ in range(numberOfChords-1):
            prevChord = nextChord(prevChord)
            chords.append(prevChord)
        return chords
            
        


def selectStartingNote():
    noteslist = [i for i in range(40, 65)]
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
def drums(sheduler):
    
    for i in range(0, sheduler.tempo.bpm*3):
        for j in range(0, 4):
            if j == 0:
                note = 42
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
                note = 35
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
            elif j == 1:
                note = 35
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
                note = 38
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
            elif j == 2:
                note = 35
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
                note = 42
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
            else:
                if i % 3 == 0:
                    note = 51
                    event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                    sheduler.addEvent(event)
                note = 35
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
                note = 38
                event = Event.Event(channel=5, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
                sheduler.addEvent(event)
            # 35 kick 38 snare 42 hat 49 cymbal

def generateChordProgression(key, scale, notes, sheduler):
    chordChannel = 1

    #chord progression
    # I – ii – iii – IV – V – vi – vii°
    numberofchords = np.random.choice([2,3,4,5], p=[0.05,0.5,0.4,0.05])
    numberofchords = 4
    nextchord = key
    chords = []

    progression = chordOrder(numberofchords)
    print(progression)
    for chord in progression:
        chords.append(key + scale[chord])

    print(chords)
    for bar in range(0, 64):

        playChordForTheKey(chords[bar%numberofchords],chordChannel,sheduler,bar,progression[bar%numberofchords])
    return progression, chords

def generateMelody(progression, chords, key, scale, notes, sheduler):
    melodyChannel = 2
    melodyNotes = []
    melodyLengths = []
    melody = []
    for bar in range(0, 64):
        if bar % 4 == 0:
            melody.append(key + scale[progression[bar%len(progression)]])
        else:
            melody.append(key + scale[np.random.choice([0,1,2,3,4,5,6])])
    for bar in range(0, 64):
        for i in range(0, 4):
            melodyNotes.append(melody[bar])
            melodyLengths.append(np.random.choice([sheduler.tempo.whole,sheduler.tempo.half,sheduler.tempo.quarter,sheduler.tempo.eighth]))
    for i in range(0, len(melodyNotes)):
        sheduler.addEvent(Event.Event(channel=melodyChannel, note=melodyNotes[i], time=i*melodyLengths[i], length=melodyLengths[i])
        )
 
        
def playChordForTheKey(note,channel,scheduler:Sheduler.Sheduler,bar,order = -1 ):

        if order == 0 or order == 3 or order == 4:

            majorChord(note, scheduler.tempo.eighth,channel,scheduler,bar)
        elif order == 1 or order == 2 or order == 5:
            
            minorChord(note, scheduler.tempo.eighth,channel,scheduler,bar)
        elif order == 6:

            diminishedChord(note,scheduler.tempo.eighth,channel,scheduler,bar)
def test(scheduler:Sheduler.Sheduler):
    for i in range(24,102):
        # print(i)
        scheduler.addEvent(Event.Event(channel=1, note=i, time=Tempo(120).quarter*(i-24), length=Tempo(120).quarter))
def startScheduler(sheduler,stop_event):

    notes = Notes.Notes()
    scale = majorScale
    key = selectStartingNote()
    # metronome(sheduler)

    # drums(sheduler)
    # progression, chords= generateChordProgression(key, scale, notes, sheduler)

    # generateMelody(progression, chords, key, scale, notes, sheduler)
    test(sheduler)
    # Start the UI
    threading.Thread(target=pygameui.startUI, args=(sheduler,stop_event)).start()
    time.sleep(1)
    sheduler.play(stop_event=stop_event)
def freeplay(sheduler):
    from pynput import keyboard
    notes = Notes.Notes().notes

    def on_press(key):
        try:
            if key.char in notes:

                sheduler.playNote(notes[key.char]-30, 1, 112)
                print(notes[key.char]-30)

            if key.char == '♥':
                listener.stop()

                return False
        except AttributeError:
            pass

    def on_release(key):

        if 'char' not in dir(key):
            return False
        if key.char in notes:
            sheduler.stopNote(notes[key.char]-30, 1)

        if key == keyboard.Key.esc:
            # Stop listener
            listener.stop()
            return False

    # Collect events until released
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()

    # ...or, in a non-blocking fashion:
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)
    listener.start()

def setInstruments(midiout):
        #piano
        midiout.send_message([0xC1, 0])
        #drums
        midiout.send_message([0xC5, 11])
        #guitar
        midiout.send_message([0xC2, 3])




def main():
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    midiout
    if available_ports:
        midiout.open_port(0)

        stop_event = threading.Event()
        sheduler = Sheduler.Sheduler(Tempo(120), midiout)
        setInstruments(midiout)
        # record.startRecording()
        threading.Thread(target=startScheduler, args=(sheduler,stop_event)).start()

        try:
            while True:
                entry = input('Press r to restart, s to save, f to freeplay, ctrl+c to exit.\n')
                if entry == 'r':
                    # record.stopRecording()
                    stop_event.set()
                    time.sleep(2)
                    # record.startRecording()
                    stop_event.clear()
                    sheduler = Sheduler.Sheduler(Tempo(120), midiout)

                    threading.Thread(target=startScheduler, args=(sheduler,stop_event)).start()
                elif entry == 's':
                    sheduler.save()
                    # record.stopRecording()
                elif entry == 'f':
                    stop_event.set()
                    freeplay(sheduler)
                    stop_event.clear()
                time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()

            

    else:
        print('No MIDI ports available')
    del midiout

if __name__ == '__main__':

    main()
