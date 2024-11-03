import time
import rtmidi
import random
import rtmidi.midiutil
import Notes
import threading
import Tempo
import Scheduler
import Event
import sys
import UIGPT as UI
# import UI
import sf2_loader as sf
import numpy as np
from perlin_noise import PerlinNoise
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
import Chords
import Freeplay
import Song
#scales
majorScale = [0, 2, 4, 5, 7, 9, 11, 12]
minorScale = [0, 2, 3, 5, 7, 8, 10, 12]
pentatonicScale = [0, 2, 5, 9, 11, 12]
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
def startScheduler(sheduler,stop_event,newSongBtnClicked,freeplayBtnClicked):

    notes = Notes.Notes()
    scale = majorScale
    key = selectStartingNote()
    # metronome(sheduler)

    Song.drums(sheduler)


    progression, chords= Song.generateChordProgression(key, scale, notes, sheduler)

    Song.generateMelody(progression, chords, key, scale, notes, sheduler)
    # test(sheduler)
    # Start the UI
    # threading.Thread(target=UI.startUI, args=(sheduler,stop_event,newSongBtnClicked,freeplayBtnClicked)).start()
    time.sleep(1)
    sheduler.play(stop_event=stop_event)

def setInstruments(midiout):
        #piano
        midiout.send_message([0xC1, 0])
        #drums
        midiout.send_message([0xC5, 11])
        #guitar
        midiout.send_message([0xC2, 3])
def test(scheduler:Scheduler.Scheduler):
    for i in range(24,102):
        # print(i)
        scheduler.addEvent(Event.Event(channel=1, note=i, time=Tempo(120).quarter*(i-24), length=Tempo(120).quarter))
def metronome(sheduler):
    for i in range(0, sheduler.tempo.bpm*3):
        for j in range(0, 4):
            if j == 0:
                note = 51
            else:
                note = 50
            event = Event.Event(channel=0, note=note , time=i*sheduler.tempo.quarter*4+(j*sheduler.tempo.quarter), length=sheduler.tempo.sixteenth)
            sheduler.addEvent(event)
def setMidiout():
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    if available_ports:
        midiout.open_port(0)
        return midiout
    else:
        print('No MIDI ports available')
    del midiout
    exit()


def main():
    midiout = setMidiout()

    stop_event = threading.Event()
    newSongBtnClicked = threading.Event()
    freeplayBtnClicked = threading.Event()
    sheduler = Scheduler.Scheduler(Tempo(80), midiout,stop_event)
    setInstruments(midiout)
    threading.Thread(target=startScheduler, args=(sheduler,stop_event,newSongBtnClicked,freeplayBtnClicked)).start()
    threading.Thread(target=UI.startUI, args=(sheduler,stop_event,newSongBtnClicked,freeplayBtnClicked)).start()

    try:
        while True:
            # entry = input('Press r to restart, s to save, f to freeplay, ctrl+c to exit.\n')
            # print(entry)
            entry = ''

            
            if newSongBtnClicked.is_set():
                print('new song')
                newSongBtnClicked.clear()
                sheduler.finalize_midi_file()
                stop_event.set()
                time.sleep(2)
                stop_event.clear()
                sheduler = Scheduler.Scheduler(Tempo(80), midiout,stop_event)
                threading.Thread(target=startScheduler, args=(sheduler,stop_event,newSongBtnClicked,freeplayBtnClicked)).start()

            elif entry == 's':

                sheduler.save()
            elif freeplayBtnClicked.is_set():
                stop_event.set()
                Freeplay.Freeplay(sheduler,newSongBtnClicked,freeplayBtnClicked)
                stop_event.clear()
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        sheduler.finalize_midi_file()
            



if __name__ == '__main__':

    main()
