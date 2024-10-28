import Event
import Scheduler
#only play one chord per bar
def simpleMajorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))
def simpleMinorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay))
def simpleDiminishedChord(note, delay, channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4

    scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay))
    scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time, length=delay))
#play a chord every quarter note
def oncePerQuarterMajorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time, length=scheduler.tempo.whole))

    for i in range(0, 4):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.quarter), length=delay))
def oncePerQuarterMinorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time, length=scheduler.tempo.whole))
    for i in range(0, 4):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.quarter), length=delay))
def oncePerQuarterDiminishedChord(note, delay, channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time, length=scheduler.tempo.whole))

    for i in range(0, 4):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.quarter), length=delay))
#play a chord every quarter note with an eighth note
def oncePerQuarterwithEighthMajorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time+(i*scheduler.tempo.eighth), length=scheduler.tempo.eighth))
        scheduler.addEvent(Event.Event(channel=channel, note=note-12 + 4, time=time+(i*scheduler.tempo.eighth), length=scheduler.tempo.eighth))

    for i in range(0, 4):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.quarter), length=delay))
def oncePerQuarterwithEighthMinorChord(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time+(i*scheduler.tempo.eighth), length=scheduler.tempo.eighth))
        scheduler.addEvent(Event.Event(channel=channel, note=note-12+3, time=time+(i*scheduler.tempo.eighth), length=scheduler.tempo.eighth))

    for i in range(0, 4):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.quarter), length=delay))
def oncePerQuarterwithEighthDiminishedChord(note, delay, channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time+(i*scheduler.tempo.eighth), length=scheduler.tempo.eighth))
        scheduler.addEvent(Event.Event(channel=channel, note=note-12+3, time=time+(i*scheduler.tempo.eighth), length=scheduler.tempo.eighth))

    for i in range(0, 4):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.quarter), length=delay))
        scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.quarter), length=delay))
# john lennon imagine
def imagineMajor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i % 2 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.eighth), length=delay))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))

        else:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
def imagineMinor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i % 2 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))

        else:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
def imagineDiminished(note, delay, channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i % 2 ==0:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.eighth), length=delay))

        else:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
# arpegio
def arpegioMajor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i %4 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 2:
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 3:
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.eighth), length=delay))
def arpegioMinor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i %4 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 2:
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 3:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
def arpegioDiminished(note, delay, channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i %4 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 2:
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 3:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
# alberti bass
def albertibassMajor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i %4 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 2:
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 3:
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))
def albertibassMinor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i %4 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 2:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 3:
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.eighth), length=delay))
def albertibassDiminished(note, delay, channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        if i %4 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 2:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.eighth), length=delay))
        if i %4 == 3:
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.eighth), length=delay))
# tresillo
def tresilloMajor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,3):
        if i %3 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time, length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay*3))

        if i %3 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(delay*3), length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(delay*3), length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(delay*3), length=delay*3))

        if i %3 == 2:

            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(delay*3*2), length=delay*2))
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(delay*3*2), length=delay*2))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(delay*3*2), length=delay*2))
def tresilloMinor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,3):
        if i %3 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time, length=delay*3))

        if i %3 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(delay*3), length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(delay*3), length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(delay*3), length=delay*3))

        if i %3 == 2:

            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(delay*3*2), length=delay*2))
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(delay*3*2), length=delay*2))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(delay*3*2), length=delay*2))
def tresilloDiminished(note, delay, channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,3):
        if i %3 == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time, length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time, length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time, length=delay*3))

        if i %3 == 1:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(delay*3), length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(delay*3), length=delay*3))
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(delay*3), length=delay*3))

        if i %3 == 2:

            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(delay*3*2), length=delay*2))
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(delay*3*2), length=delay*2))
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(delay*3*2), length=delay*2))
# turkish march
def turkishMarchMajor(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    # scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time, length=scheduler.tempo.whole))

    for i in range(0, 4):
        if i  == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        else:
            scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*scheduler.tempo.quarter), length=delay))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.quarter), length=delay))
def turkishMarchMinor(note, delay,channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    # scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time, length=scheduler.tempo.whole))
    for i in range(0, 4):
        if i == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        else:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.quarter), length=delay))
            scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*scheduler.tempo.quarter), length=delay))
def turkishMarchDiminished(note, delay, channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    # scheduler.addEvent(Event.Event(channel=channel, note=note-12, time=time, length=scheduler.tempo.whole))
    for i in range(0, 4):
        if i == 0:
            scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*scheduler.tempo.quarter), length=delay))
        else:
            scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*scheduler.tempo.quarter), length=delay))
            scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*scheduler.tempo.quarter), length=delay))
#staccato
def staccatoMajor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth
    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*delay), length=delay/2))
        scheduler.addEvent(Event.Event(channel=channel, note=note+4, time=time+(i*delay), length=delay/2))
        scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*delay), length=delay/2))
def staccatoMinor(note, delay,channel,scheduler,bar):
    delay = scheduler.tempo.eighth

    time = bar*scheduler.tempo.quarter*4
    for i in range(0,8):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*delay), length=delay/2))
        scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*delay), length=delay/2))
        scheduler.addEvent(Event.Event(channel=channel, note=note+7, time=time+(i*delay), length=delay/2))
def staccatoDiminished(note, delay, channel,scheduler,bar):
    time = bar*scheduler.tempo.quarter*4
    delay = scheduler.tempo.eighth

    for i in range(0,8):
        scheduler.addEvent(Event.Event(channel=channel, note=note, time=time+(i*delay), length=delay/2))
        scheduler.addEvent(Event.Event(channel=channel, note=note+3, time=time+(i*delay), length=delay/2))
        scheduler.addEvent(Event.Event(channel=channel, note=note+6, time=time+(i*delay), length=delay/2))

def selectRandomChordPattern():
    # get all the functions in this module
    import inspect
    import random
    import sys
    functions = inspect.getmembers(sys.modules[__name__], inspect.isfunction)

    funcs = []
    for i,function in enumerate(functions):
        if 'Major' in function[0]:
            funcs.append(functions[i])
        if 'Minor' in function[0]:
            funcs.append(functions[i])
        if 'Diminished' in function[0]:
            funcs.append(functions[i])
    funcs.sort()
    randomchords = [] 
    randomchoice= random.choice(funcs)
    if 'Diminished' in randomchoice[0]:
        randomDiminished = randomchoice
        randomMajor = funcs[funcs.index(randomchoice)+1]
        randomMinor = funcs[funcs.index(randomchoice)+2]
    if 'Major' in randomchoice[0]:
        randomDiminished = funcs[funcs.index(randomchoice)-1]
        randomMajor = randomchoice
        randomMinor = funcs[funcs.index(randomchoice)+1]
    if 'Minor' in randomchoice[0]:
        randomDiminished = funcs[funcs.index(randomchoice)-2]
        randomMajor = funcs[funcs.index(randomchoice)-1]
        randomMinor = randomchoice
    print(randomchoice[0])
    # returns major, minor, diminished in a tuple
    # return ((0,turkishMarchMajor), (0,turkishMarchMinor), (0,turkishMarchDiminished))    
    return (randomMajor, randomMinor, randomDiminished)


if __name__ == "__main__":
    selectRandomChordPattern()
