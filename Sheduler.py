import time
import datetime
import Event


class Sheduler:
    """Keep the original event queue/save format with deadline-based playback."""
    def __init__(self, tempo, midiout):
        self.tempo = tempo
        self.signature = tempo.signature
        self.midiout = midiout
        self.queue: list[Event.Event] = []
        self.time = 0

    def addEvent(self, event):
        if not 0 <= event.note <= 127 or not 0 <= event.channel <= 15:
            raise ValueError('MIDI pitch/channel out of range')
        if event.time < 0 or event.length <= 0 or not 0 <= event.velocity <= 127:
            raise ValueError('Invalid event timing or velocity')
        event.setBar(self.tempo)
        self.queue.append(event)

    def removeEvent(self, event):
        self.queue.remove(event)

    def save(self):
        now = datetime.datetime.now()
        path = 'save' + now.strftime('%d%m%Y%H%M%S') + '.queueSave'
        with open(path, 'w') as output:
            for event in self.queue:
                output.write(f'{event.channel} {event.note} {event.time} {event.length} {event.velocity}\n')
        return path

    def play(self, stop_event):
        """Schedule both note-on and note-off; retain the queue for saving/replay.

        Waiting until each actual deadline avoids losing notes between ticks.
        Note-offs precede note-ons at the same timestamp. Reference counts
        prevent one overlapping note from silencing another on the same pitch.
        """
        if self.midiout is None:
            raise ValueError('MIDI playback requires an output')
        timeline = []
        for event in self.queue:
            timeline.append((event.time, 1, event))
            timeline.append((event.time + event.length, 0, event))
        timeline.sort(key=lambda item: (item[0], item[1]))
        active = {}
        started = time.monotonic()
        try:
            for deadline, is_on, event in timeline:
                if stop_event.wait(max(0, started + deadline - time.monotonic())):
                    break
                self.time = deadline
                key = (event.channel, event.note)
                if is_on:
                    self.midiout.send_message([0x90 + event.channel, event.note, event.velocity])
                    active[key] = active.get(key, 0) + 1
                elif key in active:
                    active[key] -= 1
                    if active[key] == 0:
                        self.midiout.send_message([0x80 + event.channel, event.note, 0])
                        del active[key]
        finally:
            for channel, note in active:
                self.midiout.send_message([0x80 + channel, note, 0])
