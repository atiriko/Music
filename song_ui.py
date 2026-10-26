"""Song creator UI; composition and file formats live in song.py."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from song import Song, Section, FILL, render_song, export_song_midi, midi_preview
from piano_roll import PianoRoll


class SongPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app
        self.song = Song()
        self.bpm = tk.StringVar(value='110')
        self.name = tk.StringVar(value='A')
        self.selected = tk.StringVar()
        self.loop = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value='Capture sections from the Generator tab, then arrange them here.')
        self.playing = False
        self.job = 0
        self.cancelled = threading.Event()
        self.messages = queue.Queue()
        self.preview_update = None
        ttk.Label(self, text='Song creator', style='Title.TLabel').pack(anchor='w')
        ttk.Label(self, text='Sequence any sections: Intro - Verse - Chorus - Verse - Bridge - Chorus. Add fills where you want.').pack(anchor='w', pady=(5, 20))
        capture = ttk.Frame(self)
        capture.pack(fill='x')
        ttk.Label(capture, text='Section name').pack(side='left')
        ttk.Entry(capture, textvariable=self.name, width=12).pack(side='left', padx=8)
        ttk.Button(capture, text='Capture generator section', command=self.capture).pack(side='left')
        ttk.Label(capture, text='Song tempo (BPM)').pack(side='left', padx=(24, 8))
        ttk.Spinbox(capture, textvariable=self.bpm, from_=40, to=220, width=7).pack(side='left')
        ttk.Label(self, text='Capture stores the current generator settings and instrument choices. All sections use the song tempo.').pack(anchor='w', pady=(8, 18))
        from auto_song import LENGTHS, STYLES
        auto = ttk.LabelFrame(self, text='Automatic song creator', padding=10)
        auto.pack(fill='x', pady=(0, 12))
        self.auto_length = tk.StringVar(value='Standard')
        self.auto_style = tk.StringVar(value='From generator')
        self.auto_energy = tk.StringVar(value='65')
        self.auto_candidates = tk.StringVar(value='4')
        for col, (label, variable, choices) in enumerate([
            ('Length', self.auto_length, LENGTHS), ('Style', self.auto_style, STYLES),
        ]):
            ttk.Label(auto, text=label).grid(row=0, column=col, sticky='w')
            ttk.Combobox(auto, textvariable=variable, values=choices, state='readonly', width=18).grid(row=1, column=col, padx=(0, 10))
        ttk.Label(auto, text='Energy 0-100').grid(row=0, column=2, sticky='w')
        ttk.Spinbox(auto, textvariable=self.auto_energy, from_=0, to=100, width=8).grid(row=1, column=2, padx=6)
        ttk.Label(auto, text='Candidates 1-8').grid(row=0, column=3, sticky='w')
        ttk.Spinbox(auto, textvariable=self.auto_candidates, from_=1, to=8, width=8).grid(row=1, column=3, padx=6)
        ttk.Button(auto, text='Create and append song', command=self.create_automatic).grid(row=1, column=4, padx=10)
        self.views = ttk.Notebook(self)
        self.views.pack(fill='both', expand=True)
        arrange = ttk.Frame(self.views)
        self.views.add(arrange, text='Arrange sections')
        self.midi_roll = PianoRoll(self.views)
        self.views.add(self.midi_roll, text='MIDI output')
        content = ttk.Frame(arrange)
        content.pack(fill='both', expand=True)
        left = ttk.Frame(content)
        left.pack(side='left', fill='both', expand=True, padx=(0, 18))
        ttk.Label(left, text='Saved sections').pack(anchor='w', pady=(0, 6))
        self.sections = tk.Listbox(left, height=7, exportselection=False)
        self.sections.pack(fill='both', expand=True)
        self.sections.bind('<<ListboxSelect>>', self.select_section)
        ttk.Button(left, text='Load selected into Generator', command=self.load_section).pack(fill='x', pady=8)
        ttk.Button(left, text='Delete unused section', command=self.delete_section).pack(fill='x')
        right = ttk.Frame(content)
        right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, text='Song sequence').pack(anchor='w', pady=(0, 6))
        self.sequence = tk.Listbox(right, height=7, exportselection=False)
        self.sequence.pack(fill='both', expand=True)
        row = ttk.Frame(right)
        row.pack(fill='x', pady=8)
        self.section_choice = ttk.Combobox(row, textvariable=self.selected, values=(), state='readonly', width=10)
        self.section_choice.pack(side='left', padx=(0, 5))
        ttk.Button(row, text='Append section', command=self.append_section).pack(side='left')
        ttk.Button(row, text='Append drum fill', command=self.append_fill).pack(side='left', padx=5)
        move = ttk.Frame(right)
        move.pack(fill='x')
        for label, action in [('Move up', lambda: self.move(-1)), ('Move down', lambda: self.move(1)), ('Remove', self.remove)]:
            ttk.Button(move, text=label, command=action).pack(side='left', padx=(0, 5))
        self.timeline = tk.Canvas(arrange, height=50, background='#182238', highlightthickness=0)
        self.timeline.pack(fill='x', pady=(20, 12))
        self.timeline.bind('<Configure>', lambda event: self.refresh_timeline())
        self.total = tk.StringVar(value='0 bars')
        ttk.Label(self, textvariable=self.total, wraplength=950).pack(anchor='w')
        playback = ttk.Frame(self)
        playback.pack(fill='x', pady=(16, 10))
        for label, action in [('Play song', self.play), ('Stop', self.stop), ('Export song WAV', self.export_wav), ('Export song MIDI', self.export_midi)]:
            ttk.Button(playback, text=label, command=action).pack(side='left', padx=(0, 6))
        ttk.Checkbutton(playback, text='Loop song', variable=self.loop, command=self.change_loop).pack(side='left')
        projects = ttk.Frame(self)
        projects.pack(fill='x')
        ttk.Button(projects, text='Save song project', command=self.save).pack(side='left', padx=(0, 6))
        ttk.Button(projects, text='Open song project', command=self.open).pack(side='left')
        ttk.Label(self, text='Audio output and volume use the settings on the Generator tab.').pack(anchor='w', pady=(14, 5))
        ttk.Label(self, textvariable=self.status, wraplength=950).pack(anchor='w')
        self.bpm.trace_add('write', self.schedule_preview)
        self.after(50, self.poll)

    def create_automatic(self):
        try:
            from dataclasses import replace
            settings = replace(self.app.read_settings(), energy=int(self.auto_energy.get()))
            instruments = {part: None if var.get() == 'Mute' else var.get() for part, var in self.app.instruments.items()}
            length, style, count = self.auto_length.get(), self.auto_style.get(), int(self.auto_candidates.get())
        except Exception as error:
            self.report(error)
            return
        self.stop()
        job = self.job
        self.status.set('Composing related sections and comparing candidates...')
        def work():
            try:
                from auto_song import create
                song = create(settings, instruments, length, style, count)
                self.messages.put((job, 'composed', None, song, None))
            except Exception as error:
                self.messages.put((job, 'error', str(error), None, None))
        threading.Thread(target=work, daemon=True).start()

    def report(self, error):
        messagebox.showerror('Song creator', str(error), parent=self)

    def read_song(self):
        # Snapshot before starting work, so editing the UI cannot alter a render.
        song = Song(int(self.bpm.get()), dict(self.song.sections), list(self.song.sequence), dict(self.song.metadata))
        song.validate()
        return song

    def capture(self):
        try:
            name = self.name.get().strip()
            if name not in self.song.sections and len(self.song.sections) >= 32:
                raise ValueError('This song already has 32 sections. Update or delete one before adding another.')
            instruments = {part: None if var.get() == 'Mute' else var.get() for part, var in self.app.instruments.items()}
            section = Section(name, self.app.read_settings(), instruments)
            self.song.sections[name] = section
            self.selected.set(name)
            names = [chr(code) for code in range(65, 91)] + [f'Section{index}' for index in range(27, 33)]
            self.name.set(next((name for name in names if name not in self.song.sections), 'Section'))
            self.refresh()
            self.status.set(f'Captured section {name}: {section.settings.bars} bars in {section.settings.key} {section.settings.scale}.')
        except Exception as error:
            self.report(error)

    def select_section(self, event=None):
        selected = self.sections.curselection()
        if selected:
            name = list(self.song.sections)[selected[0]]
            self.selected.set(name)
            self.name.set(name)

    def load_section(self):
        try:
            section = self.song.sections[self.selected.get()]
            self.app.stop()
            for attr in ('key', 'scale', 'complexity', 'bpm', 'bars', 'seed',
                         'drum_style', 'drum_complexity', 'drum_fills', 'chord_style', 'bass_style', 'feel', 'phrasing', 'mix_profile', 'chord_voicing', 'strum_pattern', 'melody_style', 'countermelody'):
                getattr(self.app, attr).set(getattr(section.settings, attr))
            for part, variable in self.app.instruments.items():
                variable.set(section.instruments.get(part) or 'Mute')
            self.app.section_context = {key: getattr(section.settings, key) for key in ('hook_seed', 'section_role', 'energy')}
            self.app.notebook.select(0)
            self.app.status.set(f'Loaded section {section.name}. Press Play to hear it; capture again to update the song.')
        except Exception as error:
            self.report(error)

    def append_section(self):
        name = self.selected.get()
        if name in self.song.sections:
            self.song.sequence.append(name)
            self.refresh()
        else:
            self.status.set('Capture or select a section first.')

    def delete_section(self):
        name = self.selected.get()
        if name in self.song.sequence:
            self.status.set('Remove this section from the song sequence before deleting it.')
        elif name in self.song.sections:
            del self.song.sections[name]
            self.selected.set(next(iter(self.song.sections), ''))
            self.refresh()

    def append_fill(self):
        self.song.sequence.append(FILL)
        self.refresh()

    def move(self, direction):
        selected = self.sequence.curselection()
        if not selected:
            return
        index = selected[0]
        other = index + direction
        if 0 <= other < len(self.song.sequence):
            self.song.sequence[index], self.song.sequence[other] = self.song.sequence[other], self.song.sequence[index]
            self.refresh()
            self.sequence.selection_set(other)

    def remove(self):
        selected = self.sequence.curselection()
        if selected:
            del self.song.sequence[selected[0]]
            self.refresh()

    def refresh(self):
        if self.playing:
            self.stop()
        self.sections.delete(0, 'end')
        for name, section in self.song.sections.items():
            self.sections.insert('end', f'{name}   |   {section.settings.bars} bars   |   {section.settings.key} {section.settings.scale}')
        self.section_choice['values'] = tuple(self.song.sections)
        self.sequence.delete(0, 'end')
        start = 1
        for index, name in enumerate(self.song.sequence):
            bars = 1 if name == FILL else self.song.sections[name].settings.bars
            self.sequence.insert('end', f'{index + 1}.  {name}   |   bars {start}-{start + bars - 1}')
            start += bars
        self.total.set(f'{start - 1} bars   |   {len(self.song.sequence)} sequence entries   |   {len(self.song.sections)} saved sections')
        self.refresh_timeline()
        self.refresh_preview()

    def schedule_preview(self, *args):
        if self.playing:
            self.stop()
        if self.preview_update is not None:
            self.after_cancel(self.preview_update)
        self.preview_update = self.after(200, self.refresh_preview)

    def refresh_preview(self):
        self.preview_update = None
        try:
            self.show_midi(self.read_song())
        except (ValueError, KeyError) as error:
            self.midi_roll.set_content([])
            self.midi_roll.info.set(str(error))

    def show_midi(self, song):
        notes, boundaries = midi_preview(song)
        self.midi_roll.set_content(notes, song.bars * 4, boundaries)

    def refresh_timeline(self):
        self.timeline.delete('all')
        bars = self.song.bars
        if not bars:
            self.timeline.create_text(350, 35, text='Your song sequence will appear here', fill='#9caecb')
            return
        offset = 0
        palette = ('#70baff', '#b4a0ff', '#6edbb0', '#ffb66e')
        width = self.timeline.winfo_width()
        for name in self.song.sequence:
            count = 1 if name == FILL else self.song.sections[name].settings.bars
            left = offset / bars * width
            right = (offset + count) / bars * width
            color = '#ffb66e' if name == FILL else palette[list(self.song.sections).index(name) % len(palette)]
            self.timeline.create_rectangle(left + 1, 4, right - 1, 46, fill=color, outline='')
            self.timeline.create_text((left + right) / 2, 25, text='Fill' if name == FILL else name, fill='#182238')
            offset += count

    def cancel(self):
        self.cancelled.set()
        self.job += 1
        self.playing = False
        self.midi_roll.set_playhead(None)

    def stop(self):
        self.app.stop(announce=False)
        self.status.set('Song stopped.')

    def change_loop(self):
        if self.playing:
            self.app.player.loop = self.loop.get()

    def play(self, destination=None):
        try:
            song = self.read_song()
        except Exception as error:
            self.report(error)
            return
        self.app.stop(announce=False)
        self.show_midi(song)
        self.views.select(self.midi_roll)
        self.cancelled = threading.Event()
        cancelled, job = self.cancelled, self.job
        self.status.set('Rendering song...')
        def work():
            try:
                def progress(done, total):
                    self.messages.put((job, 'progress', (done, total), song, destination))
                audio = render_song(song, cancelled, progress)
                if audio is not None and not cancelled.is_set():
                    self.messages.put((job, 'ready', audio, song, destination))
            except Exception as error:
                self.messages.put((job, 'error', str(error), song, destination))
        threading.Thread(target=work, daemon=True).start()

    def export_wav(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.wav', filetypes=[('WAV audio', '*.wav')])
        if path:
            self.play(destination=path)

    def export_midi(self):
        try:
            song = self.read_song()
            path = filedialog.asksaveasfilename(parent=self, defaultextension='.mid', filetypes=[('MIDI music', '*.mid')])
            if path:
                self.show_midi(song)
                self.views.select(self.midi_roll)
                export_song_midi(song, path)
                self.status.set(f'Exported song MIDI: {path}')
        except Exception as error:
            self.report(error)

    def save(self):
        try:
            self.song.bpm = int(self.bpm.get())
            path = filedialog.asksaveasfilename(parent=self, defaultextension='.song.json', filetypes=[('Song project', '*.song.json')])
            if path:
                self.song.save(path)
                self.status.set(f'Saved song project: {path}')
        except Exception as error:
            self.report(error)

    def open(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[('Song project', '*.song.json'), ('JSON', '*.json')])
        if not path:
            return
        try:
            song = Song.load(path)
            self.stop()
            self.song = song
            self.bpm.set(str(song.bpm))
            self.selected.set(next(iter(song.sections), ''))
            self.refresh()
            self.status.set(f'Opened song project: {path}')
        except Exception as error:
            self.report(error)

    def poll(self):
        try:
            while True:
                job, kind, data, song, destination = self.messages.get_nowait()
                if job != self.job:
                    continue
                if kind == 'composed':
                    from auto_song import add_to_song
                    try:
                        current = Song(int(self.bpm.get()), dict(self.song.sections), list(self.song.sequence), dict(self.song.metadata))
                        song = add_to_song(current, song)
                    except Exception as error:
                        self.status.set(f'Could not append song: {error}')
                        continue
                    self.song = song
                    self.bpm.set(str(song.bpm))
                    self.selected.set(next(iter(song.sections), ''))
                    self.refresh()
                    self.show_midi(song)
                    self.views.select(self.midi_roll)
                    self.status.set(f'Created {song.bars} bars with a shared hook. Your previous sections and sequence are preserved.')
                elif kind == 'progress':
                    self.status.set(f'Rendering section {data[0]} of {data[1]}...')
                elif kind == 'error':
                    self.status.set(f'Song rendering failed: {data}')
                elif destination:
                    Path(destination).write_bytes(data)
                    self.status.set(f'Exported song WAV: {destination}')
                else:
                    try:
                        self.app.player.play_wav(data, self.app.selected_device(), self.loop.get(),
                                                 loop_duration=song.bars * 4 * 60 / song.bpm)
                        self.playing = True
                        self.active_song = song
                    except Exception as error:
                        self.status.set(f'Could not play song: {error}')
        except queue.Empty:
            pass
        except OSError as error:
            self.status.set(f'Could not export song: {error}')
        if self.playing:
            if not self.app.player.playing:
                self.playing = False
                self.midi_roll.set_playhead(None)
                self.status.set('Song finished.')
            else:
                bar = min(int(self.app.player.position / self.app.player.sample_rate * self.active_song.bpm / 240) + 1,
                          self.active_song.bars)
                self.status.set(f'Playing song: bar {bar} of {self.active_song.bars}')
                beat = self.app.player.position / self.app.player.sample_rate * self.active_song.bpm / 60
                self.midi_roll.set_playhead(beat)
        self.after(50, self.poll)
