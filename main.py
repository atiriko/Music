import time
import rtmidi
import random
from perlin_noise import PerlinNoise
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

 
def majorChord(note, delay,channel,scheduler,bar, index,numberOfChords):
    time = delay*bar*numberOfChords + delay*index
    # for i in range(0, 3):
    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))

def minorChord(note, delay,channel,scheduler,bar, index,numberOfChords):
    time = delay*bar*numberOfChords + delay*index

    
    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))

def diminishedChord(note, delay, channel,scheduler,bar, index,numberOfChords):
    time = delay*bar*numberOfChords + delay*index

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))



def generateMelody(key, midiout, tempo, scale,channel, length):
    noise = PerlinNoise()
# accepts as argument float and/or list[float]
    notes = []
    delays = []
    # print(key)
    # print(tempo.bpm)
    # print(scale)
    # print(length)
    # print(tempo.lenghts)
    possibleLengths = []
    lengthleft = length
    for leng in tempo.lenghts:
        if leng <= lengthleft:
            possibleLengths.append(len)
    
    lengthProbibilities = []
    # for i, leng in enumerate(possibleLengths):
    #     lengthProbibilities.append(abs(leng - i * 0.1))

    #scale lengthProbibilities to 1
    lengthProbibilities = [float(i)/sum(lengthProbibilities) for i in lengthProbibilities]
    print(len(possibleLengths))
    print(lengthProbibilities)
    print(np.random.choice([i in range(0,len(possibleLengths))],lengthProbibilities))
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
        print(firstChord)
        # ,[0.76,0.04,0.04,0.04,0.04,0.04,0.04]
        prevChord = firstChord
        chords = [firstChord]
        for i in range(numberOfChords-1):
            prevChord = nextChord(prevChord)
            chords.append(prevChord)
        return chords
        print(chords)
            
        
def pickNextCord(prevnote, notes, scale, key, tempo,channel, scheduler:Sheduler.Sheduler,bar, index,numberOfChords,order = -1 ):
    # print(len(scale))
    # scheduler.addEvent(Event.Event(channel=channel, note=prevnote, time=0, length=tempo.lenghts[2]*2))
    # jump = np.random.choice(scale, p=[0.2,0.1,0.15,0.2,0.2,0.1,0.05])
    # scale.index(jump)
    # if order == -1:
    #     # print(prevnote+jump)

    #     order = scale.index(jump)       
    #     if order == 0 or order == 3 or order == 4:
    #         majorChord(prevnote+jump, scheduler.tempo.whole,0,scheduler,bar, index,numberOfChords)

    #         majorChord(prevnote+jump, scheduler.tempo.whole,channel,scheduler,bar, index,numberOfChords)
    #     elif order == 1 or order == 2 or order == 5:
    #         minorChord(prevnote+jump, scheduler.tempo.whole,0,scheduler,bar, index,numberOfChords)

    #         minorChord(prevnote+jump, scheduler.tempo.whole,channel,scheduler,bar, index,numberOfChords)
    #     elif order == 6:
    #         diminishedChord(prevnote+jump, scheduler.tempo.whole,0,scheduler,bar, index,numberOfChords)

    #         diminishedChord(prevnote+jump, scheduler.tempo.whole,channel,scheduler,bar, index,numberOfChords)
    # else:
    #     # print(prevnote)
    #     # print(order)

        if order == 0 or order == 3 or order == 4:
            majorChord(prevnote, scheduler.tempo.eighth,0,scheduler,bar, index,numberOfChords)

            majorChord(prevnote, scheduler.tempo.eighth,channel,scheduler,bar, index,numberOfChords)
        elif order == 1 or order == 2 or order == 5:
            minorChord(prevnote, scheduler.tempo.eighth,0,scheduler,bar, index,numberOfChords)
            
            minorChord(prevnote, scheduler.tempo.eighth,channel,scheduler,bar, index,numberOfChords)
        elif order == 6:
            diminishedChord(prevnote,scheduler.tempo.eighth,0,scheduler,bar, index,numberOfChords)

            diminishedChord(prevnote,scheduler.tempo.eighth,channel,scheduler,bar, index,numberOfChords)

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
def generateChortProgression(key, scale, notes, sheduler):
    chordChannel = 1

    #chord progression
    # I – ii – iii – IV – V – vi – vii°
    numberofchords = np.random.choice([2,3,4,5], p=[0.05,0.5,0.4,0.05])
    numberofchords = 4
    # print(numberofchords)
    nextchord = key
    chords = []
    orders = []

    # print(chordOrder(numberofchords))
    # exit()

    progression = chordOrder(numberofchords)
    print(progression)
    for chord in progression:
        chords.append(key + scale[chord])
        orders.append(chord)
    # for i in range(0, numberofchords):
    #     nextchord, order = pickNextCord(nextchord, notes, scale, key, sheduler.tempo,chordChannel,sheduler,0,i,numberofchords)
    #     chords.append(nextchord)
    #     orders.append(order)

    for bar in range(0, numberofchords):
        # print(chors)
        # print(orders)
        for i,chord in enumerate(chords):
            pickNextCord(chord, notes, scale, key, sheduler.tempo,chordChannel,sheduler,bar,i,numberofchords,orders[i])
        

def startScheduler(sheduler,stop_event):

    notes = Notes.Notes()
    scale = minorScale
    key = selectStartingNote()
    generateChortProgression(key, scale, notes, sheduler)



    # metronome(sheduler)
    sheduler.play(stop_event=stop_event)
def setInstruments(midiout):
        midiout.send_message([0xC0, 0])
        midiout.send_message([0xC1, 35])
        midiout.send_message([0xC5, 60])
        midiout.send_message([0xC3, 117])
        midiout.send_message([0xC2, 119])

        # midiout.send_message([0xC0, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC1, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC5, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC3, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
        # midiout.send_message([0xC2, Instruments.instruments.index(np.random.choice(Instruments.instruments))])
def main():
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    midiout
    # print(available_ports)
    if available_ports:
        midiout.open_port(0)

        stop_event = threading.Event()
        sheduler = Sheduler.Sheduler(Tempo(120), midiout)
        setInstruments(midiout)

        threading.Thread(target=startScheduler, args=(sheduler,stop_event)).start()

        try:
            while True:
                entry = input('Press r to restart, s to save, ctrl+c to stop.\n')
                if entry == 'r':
                    stop_event.set()
                    time.sleep(2)
                    stop_event.clear()
                    sheduler = Sheduler.Sheduler(Tempo(120), midiout)

                    threading.Thread(target=startScheduler, args=(sheduler,stop_event)).start()
                elif entry == 's':
                    sheduler.save()
                time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()

            

    else:
        print('No MIDI ports available')
    del midiout

if __name__ == '__main__':
    main()
