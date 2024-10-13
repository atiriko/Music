import time
import datetime
import Event
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
class Sheduler:
    def __init__(self, tempo, midiout):
        self.tempo = tempo
        self.signature = tempo.signature
        self.midiout = midiout
        self.queue:list[Event.Event] = []
        self.time = 0
    

    
    def addEvent(self, event):
        event.setBar(self.tempo)
        self.queue.append(event)
    def removeEvent(self, event):
        self.queue.remove(event)
    def save(self):
        dt = datetime.datetime
        now = dt.now()
        with open('save'+dt.strftime(now,"%d%m%Y%H%M%S") + '.queueSave','w') as f:
            for event in self.queue:
                f.write(str(event.channel)+' ')
                f.write(str(event.note)+' ')
                f.write(str(event.time)+' ')
                f.write(str(event.length)+' ')
                f.write(str(event.velocity)+'\n')
    def getMinNote(self):
        min = 200
        for event in self.queue:
            if event.note < min:
                min = event.note
        return min
    def getMaxNote(self):
        maxNote = -1
        for event in self.queue:
            if event.note > maxNote:
                maxNote = event.note
        return maxNote
    def printQueue(self):
        for event in self.queue:
            print(event)
    def playNote(self, note, channel, velocity, length=1):
        # print(note)
        pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'beat':True}))

        pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'noteOn':True,'channel':channel,'note':note,'velocity':velocity, 'length':length}))
        self.midiout.send_message([0x90 + channel, note, velocity])
    def stopNote(self, note, channel):
        pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'beat':True}))

        pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'noteOn':False,'channel':channel,'note':note}))

        self.midiout.send_message([0x80 + channel, note, 0])
            
    def play(self,stop_event):
        while not stop_event.is_set():
            self.queue.sort()
            notesThisBeat = []

            for event in self.queue:
                if round(event.time,3) == round(self.time,3): 
                    notesThisBeat.append(event)
            
            self.time += self.tempo.thirtysecond

            for note in notesThisBeat:
                self.playNote(note.note,note.channel,note.velocity,note.length)
                


            for note in notesThisBeat:
                if round(self.time,3) == round(note.time,3) + round(note.length,3):
                    self.stopNote(note.note,note.channel,note.velocity)
                    notesThisBeat.remove(note)
                    self.queue.remove(note)
            # print((self.time % (self.tempo.bpm/60))%0.5 == 0)
            # if (self.time % (self.tempo.bpm/60))%0.25 == 0:
   
            time.sleep(self.tempo.thirtysecond)
           

