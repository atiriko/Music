"""Scrollable MIDI piano roll for the assembled song; no audio generation here."""
import tkinter as tk
from tkinter import ttk

COLORS = {'Melody': '#70baff', 'Chords': '#b4a0ff', 'Bass': '#6edbb0', 'Drums': '#ffb66e'}


class PianoRoll(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.notes = []
        self.boundaries = []
        self.total_beats = 4
        self.beat = None
        self.part = tk.StringVar(value='All parts')
        self.zoom = tk.StringVar(value='Fit song')
        self.follow = tk.BooleanVar(value=True)
        self.info = tk.StringVar(value='Add sections to see the complete song as MIDI notes.')
        controls = ttk.Frame(self)
        controls.pack(fill='x', padx=8, pady=6)
        ttk.Label(controls, text='Track').pack(side='left')
        track = ttk.Combobox(controls, textvariable=self.part, values=('All parts',) + tuple(COLORS), state='readonly', width=12)
        track.pack(side='left', padx=(6, 16))
        ttk.Label(controls, text='View').pack(side='left')
        zoom = ttk.Combobox(controls, textvariable=self.zoom, values=('Fit song', '4 bars', '8 bars', '16 bars'), state='readonly', width=10)
        zoom.pack(side='left', padx=6)
        ttk.Checkbutton(controls, text='Follow playback', variable=self.follow).pack(side='left', padx=10)
        self.canvas = tk.Canvas(self, background='#182238', highlightthickness=0, height=150)
        self.canvas.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        scrollbar.pack(fill='x')
        self.canvas.configure(xscrollcommand=scrollbar.set)
        ttk.Label(self, textvariable=self.info, wraplength=950).pack(anchor='w', padx=8, pady=5)
        self.canvas.bind('<Configure>', lambda event: self.draw())
        track.bind('<<ComboboxSelected>>', lambda event: self.draw())
        zoom.bind('<<ComboboxSelected>>', lambda event: self.draw())

    def set_content(self, notes, total_beats=4, boundaries=()):
        self.notes = list(notes)
        self.total_beats = max(4, total_beats)
        self.boundaries = list(boundaries)
        self.info.set(f'{len(self.notes)} MIDI notes | {self.total_beats / 4:g} bars | Blue: melody; purple: chords; green: bass; orange: drums. Click a note for details.')
        self.draw()

    def draw(self):
        self.canvas.delete('all')
        viewport = max(100, self.canvas.winfo_width())
        height = max(100, self.canvas.winfo_height())
        bars = self.total_beats / 4
        visible_bars = bars if self.zoom.get() == 'Fit song' else int(self.zoom.get().split()[0])
        self.pixels_per_beat = (viewport - 48) / (visible_bars * 4)
        width = max(viewport, self.total_beats * self.pixels_per_beat + 48)
        self.canvas.configure(scrollregion=(0, 0, width, height))
        selected = [note for note in self.notes if self.part.get() == 'All parts' or note.part == self.part.get()]
        if not selected:
            self.canvas.create_text(viewport / 2, height / 2, text='No MIDI notes in this view.', fill='#9caecb')
            return
        low = min(note.pitch for note in selected) - 2
        high = max(note.pitch for note in selected) + 2
        row = (height - 55) / (high - low + 1)
        for pitch in range(low, high + 1):
            if pitch % 12 == 0:
                y = 42 + (high - pitch) * row
                self.canvas.create_line(0, y, width, y, fill='#2a3852')
                self.canvas.create_text(3, y - 6, anchor='w', text=f'C{pitch // 12 - 1}', fill='#9caecb', font=('Segoe UI', 8))
        label_step = max(1, int(visible_bars / 16))
        for bar in range(int(bars) + 1):
            x = 38 + bar * 4 * self.pixels_per_beat
            self.canvas.create_line(x, 28, x, height, fill='#34415a')
            if bar < bars and bar % label_step == 0:
                self.canvas.create_text(x + 3, 25, anchor='w', text=str(bar + 1), fill='#9caecb', font=('Segoe UI', 8))
        for index, (start, name) in enumerate(self.boundaries):
            end = self.boundaries[index + 1][0] if index + 1 < len(self.boundaries) else self.total_beats
            x = 38 + start * self.pixels_per_beat
            right = 38 + end * self.pixels_per_beat
            self.canvas.create_rectangle(x, 0, right, 17, fill='#34415a' if index % 2 else '#29364e', outline='')
            self.canvas.create_text(x + 4, 8, anchor='w', text=name, fill='#d8e2f5', font=('Segoe UI', 8))
        for note in selected:
            x = 38 + note.beat * self.pixels_per_beat
            end = 38 + (note.beat + note.duration) * self.pixels_per_beat
            y = 42 + (high - note.pitch) * row
            rectangle = self.canvas.create_rectangle(x, y - max(1, row * .35), max(x + 2, end), y + max(1, row * .35),
                                                     fill=COLORS[note.part], outline='', tags='midi-note')
            self.canvas.tag_bind(rectangle, '<Button-1>', lambda event, n=note: self.describe(n))
        self.set_playhead(self.beat, scroll=False)

    def describe(self, note):
        self.info.set(f'{note.part} | MIDI note {note.pitch} | Bar {int(note.beat // 4) + 1}, beat {note.beat % 4 + 1:g} | Length {note.duration:g} beats')

    def set_playhead(self, beat, scroll=True):
        self.beat = beat
        self.canvas.delete('playhead')
        if beat is None or not hasattr(self, 'pixels_per_beat'):
            return
        x = 38 + min(beat, self.total_beats) * self.pixels_per_beat
        self.canvas.create_line(x, 18, x, self.canvas.winfo_height(), fill='white', width=2, tags='playhead')
        if scroll and self.follow.get():
            left = self.canvas.canvasx(0)
            viewport = self.canvas.winfo_width()
            if x < left + 20 or x > left + viewport - 20:
                total = self.total_beats * self.pixels_per_beat + 48
                self.canvas.xview_moveto(max(0, (x - 38) / total))
