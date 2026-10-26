import Tempo
class Event:
    def __init__(self, channel, note, time,length, velocity = 112):
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.time = time
        self.length = length
        self.bar = 0
    def setBar(self, tempo:Tempo):
        bar_length = tempo.quarter * tempo.signatureTop * 4 / tempo.signatureBottom
        self.bar = self.time / bar_length
        return self.bar
    def __cmp__(self, other):
        return self.time - other.time
    def __le__(self, other):
        return self.time <= other.time
    def __ge__(self, other):    
        return self.time >= other.time
    def __lt__(self, other):
        return self.time < other.time
    def __gt__(self, other):
        return self.time > other.time
    def __str__(self) -> str:
        return f"Event: {self.note} at {self.time} for {self.length} seconds"
