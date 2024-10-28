import numpy as np
import Chords
import Event
import Scheduler

def playChordForTheKey(note,channel,scheduler:Scheduler.Scheduler,bar,order = -1 , chordPatterns = None):
        # print(randomChordPatterns[0])
        if order == 0 or order == 3 or order == 4:
            # chords.simpleMajorChord(note, scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.oncePerQuarterMajorChord(note,scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.oncePerQuarterMajorChordwithEighth(note,scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.imagineMajor(note,scheduler.tempo.eighth,channel,scheduler,bar)
            # chords.arpegioMajor(note, scheduler.tempo.eighth,channel,scheduler,bar)
            chordPatterns[0](note, scheduler.tempo.quarter,channel,scheduler,bar)
        elif order == 1 or order == 2 or order == 5:
            # chords.simpleMinorChord(note, scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.oncePerQuarterMinorChord(note,scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.oncePerQuarterMinorChordwithEighth(note,scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.imagineMinor(note,scheduler.tempo.eighth,channel,scheduler,bar)
            # chords.arpegioMinor(note, scheduler.tempo.eighth,channel,scheduler,bar)
            chordPatterns[1](note, scheduler.tempo.quarter,channel,scheduler,bar)
        elif order == 6:
            # chords.simpleDiminishedChord(note, scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.oncePerQuarterDiminishedChord(note,scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.oncePerQuarterDiminishedChordwithEighth(note,scheduler.tempo.quarter,channel,scheduler,bar)
            # chords.imagineDiminished(note,scheduler.tempo.eighth,channel,scheduler,bar)
            # chords.arpegioDiminished(note,scheduler.tempo.eighth,channel,scheduler,bar)
            chordPatterns[2](note, scheduler.tempo.quarter,channel,scheduler,bar)
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
    randomChordPatterns =Chords.selectRandomChordPattern()

    major, minor, diminished = (randomChordPatterns[0][1], randomChordPatterns[1][1], randomChordPatterns[2][1])
    for bar in range(0, 64):

        playChordForTheKey(chords[bar%numberofchords],chordChannel,sheduler,bar,progression[bar%numberofchords],(major,minor,diminished))
    return progression, chords
            
        




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
        sheduler.addEvent(Event.Event(channel=melodyChannel, note=melodyNotes[i], time=i*melodyLengths[i], length=melodyLengths[i]))
 