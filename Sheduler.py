import time
import datetime
import Event 
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
        # Event.Event(
        with open('save'+dt.strftime(now,"%d%m%Y%H%M%S") + '.queueSave','w') as f:
            for event in self.queue:
                f.write(str(event.channel)+' ')
                f.write(str(event.note)+' ')
                f.write(str(event.time)+' ')
                f.write(str(event.length)+' ')
                f.write(str(event.velocity)+'\n')
    
    def printQueue(self):
        for event in self.queue:
            print(event)
            
    def play(self,stop_event):
        # for event in self.queue:
        #     print(event)

        while not stop_event.is_set():
            self.queue.sort()
            # print(self.time)
            notesThisBeat = []
            for event in self.queue:
                # print(event)
                if round(event.time,3) == round(self.time,3): 
                    notesThisBeat.append(event)
            
            self.time += self.tempo.thirtysecond
            # if not notesThisBeat:
            #     continue
            for note in notesThisBeat:
                self.midiout.send_message([0x90 + note.channel, note.note, note.velocity])
            # time.sleep(notesThisBeat[0].length)

            for note in notesThisBeat:
                if round(self.time,3) == round(note.time,3) + round(note.length,3):
                    self.midiout.send_message([0x80 + note.channel, note.note, 0])
                    notesThisBeat.remove(note)
                    self.queue.remove(note)   
            time.sleep(self.tempo.thirtysecond)
           

