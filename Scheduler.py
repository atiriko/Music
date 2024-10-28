import time
import datetime
import Event
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
import mido
from mido import MidiFile, MidiTrack
import Freeplay
import Tempo
import threading 
class Scheduler:
    def __init__(self, tempo, midiout,stop_event):
        self.tempo = tempo
        self.signature = tempo.signature
        self.midiout = midiout
        self.queue:list[Event.Event] = []
        self.time = 0
                # Initialize MIDI file
        self.midi_file = None
        self.current_track = None
        self.initialize_midi_file("output.mid")
        self.last_time = 0
        self.stop_event = stop_event


    
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
        # pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'beat':True}))
        # Convert to milliseconds
        delta_time = int(self.time*1000 - self.last_time*1000)
        # print(self.time*100, self.last_time*100,delta_time)

        pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'noteOn':True,'channel':channel,'note':note,'velocity':velocity, 'length':length}))
        self.midiout.send_message([0x90 + channel, note, velocity])
        self.current_track.append(mido.Message('note_on', note=note, channel=channel, velocity=velocity,time=delta_time))
        self.last_time = self.time 

    def stopNote(self, note, channel):
        # pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'beat':True}))
        current_time = self.time  # Convert to milliseconds
        delta_time = int(current_time*1000 - self.last_time*1000)
        pygame.event.post(pygame.event.Event(pygame.event.custom_type(),{'noteOn':False,'channel':channel,'note':note}))

        self.midiout.send_message([0x80 + channel, note, 0])
        self.current_track.append(mido.Message('note_off', note=note, channel=channel,time=delta_time))
        self.last_time = self.time 

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
           

    def initialize_midi_file(self, filename):
        self.midi_file = MidiFile()
        self.current_track = MidiTrack()
        self.midi_file.tracks.append(self.current_track)

    def _write_midi_event(self, note, channel, velocity, length=1):
        timestamp = int(self.time * 1000)  # Convert to milliseconds
        self.current_track.append(mido.Message('note_on', note=note, channel=channel, velocity=velocity))
        self.current_track.append(mido.Message('note_off', note=note, channel=channel))
    def freeplay(self):
        self.stop()

        Freeplay.Freeplay(self)
    def stop(self):
        self.stop_event.set()
    def start(self):
        self.stop_event.clear()
        sheduler = Scheduler(Tempo.Tempo(120), self.midiout,self.stop_event)
        threading.Thread(target=self.startScheduler, args=(sheduler,self.stop_event)).start()


    def finalize_midi_file(self):

        if self.midi_file:
            # self.midi_file.print_tracks()
            self.midi_file.save("output.mid")
            # self.midi_file.close()




