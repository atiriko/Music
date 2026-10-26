"""Tk desktop controls and Windows audio playback."""
from pathlib import Path
from dataclasses import replace
import queue
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from audio_output import AudioPlayer

from generator import KEYS, SCALES, COMPLEXITIES, Settings, generate
from accompaniment import CHORD_STYLES, BASS_STYLES
from phrasing import PHRASINGS
from performance import FEELS
from drum_patterns import DRUM_STYLES, DRUM_COMPLEXITIES, DRUM_FILLS
from synth import INSTRUMENTS, render
from Instruments import DRUM_KITS
from instrument_picker import InstrumentPicker, import_dialog
from mix_settings import MIX_PROFILES
from generator import MELODY_STYLES
from accompaniment import VOICINGS, STRUMS
from scroll_frame import ScrollablePage
from presets import SOUND_PRESETS
from midi_export import save_midi
from song_ui import SongPanel


class MusicApp:
    def __init__(self, root):
        self.root = root
        root.title('Algorithmic Royalty Free Music Maker')
        width = min(1100, root.winfo_screenwidth() - 40)
        height = min(900, root.winfo_screenheight() - 100)
        root.geometry(f'{width}x{height}+20+20')
        root.minsize(min(1020, width), min(780, height))
        self.messages = queue.Queue()
        self.cancelled = threading.Event()
        self.job = 0
        self.playing = False
        self.instrument_update = None
        self.duration = 1
        self.player = AudioPlayer()
        self.audio = None
        self.devices = self.player.devices()
        self.output = tk.StringVar(value=self.player.preferred_device(self.devices))
        self.volume = tk.DoubleVar(value=80)
        self.key = tk.StringVar(value='C')
        self.scale = tk.StringVar(value='Major')
        self.complexity = tk.StringVar(value='Balanced')
        self.bpm = tk.StringVar(value='110')
        self.bars = tk.StringVar(value='8')
        self.seed = tk.StringVar(value=str(random.randrange(1_000_000)))
        self.loop = tk.BooleanVar(value=True)
        self.drum_style = tk.StringVar(value='Rock')
        self.drum_complexity = tk.StringVar(value='Follow complexity')
        self.drum_fills = tk.StringVar(value='Every 4 bars')
        self.chord_style = tk.StringVar(value='Varied')
        self.bass_style = tk.StringVar(value='Varied')
        self.feel = tk.StringVar(value='Natural')
        self.phrasing = tk.StringVar(value='Balanced')
        self.mix_profile = tk.StringVar(value='Balanced')
        self.chord_voicing = tk.StringVar(value='Auto')
        self.strum_pattern = tk.StringVar(value='Auto')
        self.melody_style = tk.StringVar(value='Motivic')
        self.countermelody = tk.BooleanVar(value=False)
        self.sound_preset = tk.StringVar(value='Studio band')
        self.instrument_search = tk.StringVar()
        self.instrument_pickers = []
        self.section_context = {}
        self.instruments = {part: tk.StringVar(value=voice) for part, voice in
                            [('Melody', 'Studio Upright'), ('Chords', 'Studio Clean Guitar'), ('Bass', 'Finger Bass'), ('Countermelody', 'Flute'), ('Drums', 'Room kit')]}
        self.status = tk.StringVar(value='Choose your sound, then press Play.')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#f2f4f8')
        style.configure('TLabel', background='#f2f4f8', foreground='#182238')
        style.configure('Title.TLabel', font=('Segoe UI', 23, 'bold'))
        style.configure('TButton', padding=(14, 8))
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        page = ScrollablePage(self.notebook)
        frame = page.body
        self.notebook.add(page, text='Generator')
        ttk.Label(frame, text='Algorithmic Royalty Free Music Maker', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Compose in a key. Shape the detail. Play with built-in sounds.').pack(anchor='w', pady=(4, 20))
        controls = ttk.Frame(frame)
        controls.pack(fill='x')
        for column in range(3):
            controls.columnconfigure(column, weight=1)
        for col, (label, variable, choices) in enumerate([
            ('Key', self.key, KEYS), ('Scale', self.scale, tuple(SCALES)),
            ('Complexity', self.complexity, COMPLEXITIES),
        ]):
            self.choice(controls, label, variable, choices, 0, col)
        for col, (label, variable, lower, upper) in enumerate([
            ('Tempo (BPM)', self.bpm, 40, 220), ('Length (bars)', self.bars, 1, 32),
            ('Variation seed', self.seed, 0, 999999999),
        ]):
            ttk.Label(controls, text=label).grid(row=2, column=col, sticky='w', pady=(14, 5))
            ttk.Spinbox(controls, textvariable=variable, from_=lower, to=upper).grid(row=3, column=col, sticky='ew', padx=(0, 14))
        ttk.Label(frame, text='Simple: spacious  |  Balanced: flowing  |  Intricate: faster rhythms and richer chords').pack(anchor='w', pady=(12, 16))
        voices = ttk.Frame(frame)
        voices.pack(fill='x')
        for col, (part, variable) in enumerate(self.instruments.items()):
            voices.columnconfigure(col, weight=1)
            choices = tuple(DRUM_KITS) if part == 'Drums' else INSTRUMENTS
            picker = InstrumentPicker(voices, part, variable, self.instrument_search)
            picker.grid(row=0, column=col, sticky='ew', padx=(0, 14))
            self.instrument_pickers.append(picker)
        library_row = ttk.Frame(frame)
        library_row.pack(fill='x', pady=(8, 10))
        ttk.Button(library_row, text='Import instruments (.sf2)', command=lambda: import_dialog(self)).pack(side='left')
        ttk.Label(library_row, text='Search instruments').pack(side='left', padx=(14, 6))
        ttk.Entry(library_row, textvariable=self.instrument_search, width=18).pack(side='left')
        preset_box = ttk.Combobox(library_row, textvariable=self.sound_preset, values=tuple(SOUND_PRESETS), state='readonly', width=16)
        preset_box.pack(side='left', padx=(16, 6))
        ttk.Button(library_row, text='Load sound preset', command=self.apply_sound_preset).pack(side='left')
        drum_controls = ttk.Frame(frame)
        drum_controls.pack(fill='x', pady=(0, 12))
        for col, (label, variable, choices) in enumerate([
            ('Drum style', self.drum_style, DRUM_STYLES),
            ('Drum complexity', self.drum_complexity, DRUM_COMPLEXITIES),
            ('Drum fills', self.drum_fills, tuple(DRUM_FILLS)),
        ]):
            drum_controls.columnconfigure(col, weight=1)
            self.choice(drum_controls, label, variable, choices, 0, col)
        playing_controls = ttk.Frame(frame)
        playing_controls.pack(fill='x', pady=(0, 12))
        for col, (label, variable, choices) in enumerate([
            ('Chord pattern', self.chord_style, CHORD_STYLES),
            ('Bass pattern', self.bass_style, BASS_STYLES),
            ('Playing feel', self.feel, FEELS),
            ('Phrasing / space', self.phrasing, PHRASINGS),
            ('Mix', self.mix_profile, MIX_PROFILES),
        ]):
            playing_controls.columnconfigure(col, weight=1)
            self.choice(playing_controls, label, variable, choices, 0, col)
        phrase_controls = ttk.Frame(frame)
        phrase_controls.pack(fill='x', pady=(0, 12))
        for col, (label, variable, choices) in enumerate([
            ('Chord voicing', self.chord_voicing, VOICINGS),
            ('Strum pattern', self.strum_pattern, STRUMS),
            ('Melody character', self.melody_style, MELODY_STYLES),
        ]):
            phrase_controls.columnconfigure(col, weight=1)
            self.choice(phrase_controls, label, variable, choices, 0, col)
        ttk.Checkbutton(phrase_controls, text='Second melody / counterpoint', variable=self.countermelody).grid(row=1, column=3, padx=10)
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x')
        ttk.Button(buttons, text='Play', command=self.start).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='New variation', command=self.new_variation).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Stop', command=self.stop).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Export WAV', command=self.export).pack(side='left')
        ttk.Button(buttons, text='Export MIDI', command=self.export_midi).pack(side='left', padx=(8, 0))
        ttk.Checkbutton(buttons, text='Loop full piece', variable=self.loop, command=self.update_loop).pack(side='right')
        audio_controls = ttk.Frame(frame)
        audio_controls.pack(fill='x', pady=(14, 0))
        ttk.Label(audio_controls, text='Audio output').grid(row=0, column=0, sticky='w')
        self.output_box = ttk.Combobox(audio_controls, textvariable=self.output,
                                      values=tuple(self.devices), state='readonly')
        self.output_box.grid(row=1, column=0, sticky='ew', padx=(0, 8))
        audio_controls.columnconfigure(0, weight=1)
        ttk.Button(audio_controls, text='Test sound', command=self.test_sound).grid(row=1, column=1, padx=4)
        ttk.Button(audio_controls, text='Refresh outputs', command=self.refresh_outputs).grid(row=1, column=2, padx=4)
        ttk.Label(audio_controls, text='Volume').grid(row=0, column=3, sticky='w')
        ttk.Scale(audio_controls, variable=self.volume, from_=0, to=100,
                  command=self.change_volume, length=130).grid(row=1, column=3, padx=(10, 0))
        self.canvas = tk.Canvas(frame, height=100, background='#182238', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, pady=(20, 10))
        self.canvas.bind('<Configure>', lambda event: self.draw())
        self.notes = []
        self.settings = Settings()
        self.progress = ttk.Progressbar(frame, maximum=100)
        self.progress.pack(fill='x')
        ttk.Label(frame, textvariable=self.status, wraplength=820).pack(anchor='w', pady=(10, 0))
        ttk.Label(frame, text='Melody: blue     Chords: purple     Bass: green     Drums: orange  |  Instruments and drum controls update during playback.').pack(anchor='w', pady=(7, 0))
        self.song_panel = SongPanel(self.notebook, self)
        self.notebook.add(self.song_panel, text='Song creator')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.countermelody.trace_add('write', self.sync_countermelody)
        self.sync_countermelody()
        for variable in (*self.instruments.values(), self.drum_style, self.drum_complexity, self.drum_fills, self.chord_style, self.bass_style, self.feel, self.phrasing, self.mix_profile, self.chord_voicing, self.strum_pattern, self.melody_style, self.countermelody):
            variable.trace_add('write', self.instruments_changed)
        root.after(50, self.poll)

    @staticmethod
    def choice(parent, label, variable, choices, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky='w', pady=(0, 5))
        ttk.Combobox(parent, textvariable=variable, values=choices, state='readonly', height=18).grid(row=row + 1, column=col, sticky='ew', padx=(0, 14))

    def apply_sound_preset(self):
        preset = SOUND_PRESETS[self.sound_preset.get()]
        for part, name in preset['instruments'].items():
            self.instruments[part].set(name)
        for key, value in preset['settings'].items():
            getattr(self, key).set(value)
        self.status.set('Loaded ' + self.sound_preset.get() + '. Every setting remains editable.')

    def sync_countermelody(self, *_):
        for picker in self.instrument_pickers:
            if picker.part == 'Countermelody':
                picker.set_enabled(self.countermelody.get())

    def read_settings(self):
        try:
            return Settings(self.key.get(), self.scale.get(), self.complexity.get(),
                            int(self.bpm.get()), int(self.bars.get()), int(self.seed.get()),
                            self.drum_style.get(), self.drum_complexity.get(), self.drum_fills.get(),
                            self.chord_style.get(), self.bass_style.get(), self.feel.get(), self.phrasing.get(),
                            mix_profile=self.mix_profile.get(), chord_voicing=self.chord_voicing.get(),
                            strum_pattern=self.strum_pattern.get(), melody_style=self.melody_style.get(),
                            countermelody=self.countermelody.get(), **self.section_context)
        except ValueError as error:
            raise ValueError('Use whole numbers for tempo, bars, and seed. ' + str(error)) from error

    def start(self, destination=None, keep_position=False):
        try:
            settings = self.read_settings()
            instruments = {part: (None if var.get() == 'Mute' else var.get())
                           for part, var in self.instruments.items()}
            if not any(instruments.values()) and not keep_position:
                raise ValueError('Choose an instrument for at least one part.')
        except ValueError as error:
            messagebox.showerror('Check settings', str(error), parent=self.root)
            return
        if keep_position:
            self.cancelled.set()
            self.cancelled = threading.Event()
            self.job += 1
        else:
            self.stop(announce=False)
        job = self.job
        cancelled = self.cancelled
        self.status.set('Rendering your composition...')

        def work():
            try:
                notes = generate(settings, instruments)
                audio = render(notes, settings, instruments, cancelled)
                if audio is not None and not cancelled.is_set():
                    self.messages.put((job, settings, notes, audio, destination, None, keep_position))
            except Exception as error:
                self.messages.put((job, settings, [], None, destination, str(error), keep_position))
        threading.Thread(target=work, daemon=True).start()

    def new_variation(self):
        try:
            settings = self.read_settings()
        except ValueError:
            self.start()
            return
        def rhythm(notes):
            return [(round(note.beat, 6), note.pitch) for note in notes if note.part == 'Drums']
        previous = rhythm(generate(replace(settings, feel='Tight')))
        # Avoid drawing the same groove again, including in one-bar sections.
        for _ in range(32):
            seed = random.randrange(1_000_000_000)
            if rhythm(generate(replace(settings, seed=seed, feel='Tight'))) != previous:
                break
        self.seed.set(str(seed))
        self.start()

    def instruments_changed(self, *args):
        if self.instrument_update is not None:
            self.root.after_cancel(self.instrument_update)
        self.instrument_update = self.root.after(200, self.apply_instruments)

    def apply_instruments(self):
        self.instrument_update = None
        if self.playing:
            self.start(keep_position=True)

    def stop(self, announce=True):
        if hasattr(self, 'song_panel'):
            self.song_panel.cancel()
        if self.instrument_update is not None:
            self.root.after_cancel(self.instrument_update)
            self.instrument_update = None
        self.cancelled.set()
        self.cancelled = threading.Event()
        self.job += 1
        self.player.stop()
        self.playing = False
        self.progress['value'] = 0
        self.canvas.delete('playhead')
        if announce:
            self.status.set('Stopped. Press Play to replay this variation.')

    def export(self):
        path = filedialog.asksaveasfilename(parent=self.root, title='Export current settings as WAV',
                                          defaultextension='.wav', filetypes=[('WAV audio', '*.wav')])
        if path:
            self.start(destination=path)

    def selected_device(self):
        if self.output.get() not in self.devices:
            raise ValueError('Select an available audio output, then try Test sound.')
        self.player.volume = self.volume.get() / 100
        self.player.remember_device(self.output.get())
        return self.devices[self.output.get()]

    def export_midi(self):
        try:
            settings = self.read_settings()
            instruments = {part: None if variable.get() == 'Mute' else variable.get()
                           for part, variable in self.instruments.items()}
            path = filedialog.asksaveasfilename(parent=self.root, title='Export arrangement as MIDI',
                                              defaultextension='.mid', filetypes=[('MIDI music', '*.mid')])
            if path:
                save_midi(path, generate(settings, instruments), settings, instruments)
                self.status.set(f'Exported MIDI: {path}')
        except Exception as error:
            messagebox.showerror('MIDI export failed', str(error), parent=self.root)

    def play_file(self, start_time=0):
        self.player.play_wav(self.audio, self.selected_device(), self.loop.get(),
                             loop_duration=self.settings.bars * 4 * 60 / self.settings.bpm,
                             start_time=start_time)
        self.playing = True

    def change_volume(self, value):
        self.player.volume = float(value) / 100

    def test_sound(self):
        self.stop(announce=False)
        try:
            self.player.test_tone(self.selected_device())
            self.status.set(f'Test tone sent to {self.output.get()}. If silent, check that output and its volume.')
        except Exception as error:
            self.status.set(f'Audio output failed: {error}')

    def refresh_outputs(self):
        try:
            self.devices = self.player.devices()
            self.output_box['values'] = tuple(self.devices)
            if self.output.get() not in self.devices:
                self.output.set(self.player.preferred_device(self.devices))
        except Exception as error:
            self.status.set(f'Could not list outputs: {error}')

    def update_loop(self):
        self.player.loop = self.loop.get()

    def poll(self):
        try:
            while True:
                job, settings, notes, audio, destination, error, keep_position = self.messages.get_nowait()
                if job != self.job:
                    continue
                if error:
                    self.status.set(f'Rendering failed: {error}')
                    continue
                self.settings, self.notes = settings, notes
                self.draw()
                try:
                    if destination:
                        Path(destination).write_bytes(audio)
                        self.status.set(f'Exported WAV: {destination}')
                    else:
                        self.audio = audio
                        self.duration = settings.bars * 4 * 60 / settings.bpm
                        position = self.player.position / self.player.sample_rate if keep_position and self.playing else 0
                        self.play_file(start_time=position)
                        self.status.set(f'Playing {settings.key} {settings.scale.lower()} | {settings.complexity} | {settings.bpm} BPM | Output: {self.output.get()}')
                except Exception as error:
                    self.status.set(f'Could not save or play audio: {error}')
        except queue.Empty:
            pass
        if self.playing:
            if not self.player.playing:
                self.playing = False
                self.status.set('Finished. Play again or try a new variation.')
                self.progress['value'] = 100
                self.canvas.delete('playhead')
            else:
                position = self.player.position / self.player.sample_rate
                fraction = min(position / self.duration, 1)
                bar = min(int(position / (4 * 60 / self.settings.bpm)) + 1, self.settings.bars)
                self.status.set(f'Playing bar {bar} of {self.settings.bars} | '
                                f'{self.settings.key} {self.settings.scale.lower()} | '
                                f'{self.settings.bpm} BPM | Output: {self.output.get()}')
                self.progress['value'] = fraction * 100
                self.canvas.delete('playhead')
                x = 12 + fraction * (self.canvas.winfo_width() - 24)
                self.canvas.create_line(x, 0, x, self.canvas.winfo_height(), fill='white', tags='playhead')
        self.root.after(50, self.poll)

    def draw(self):
        self.canvas.delete('all')
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if not self.notes:
            self.canvas.create_text(width / 2, height / 2, text='Your composition will appear here', fill='#9caecb', font=('Segoe UI', 12))
            return
        total = self.settings.bars * 4
        low = min(n.pitch for n in self.notes) - 2
        high = max(n.pitch for n in self.notes) + 2
        for bar in range(self.settings.bars + 1):
            x = 12 + bar * (width - 24) / self.settings.bars
            self.canvas.create_line(x, 0, x, height, fill='#2a3852')
        for note in self.notes:
            x = 12 + note.beat / total * (width - 24)
            y = 10 + (high - note.pitch) / (high - low) * (height - 20)
            end = x + note.duration / total * (width - 24)
            self.canvas.create_rectangle(x, y - 2, max(x + 2, end), y + 2,
                                         fill={'Melody': '#70baff', 'Countermelody': '#f4d87d', 'Chords': '#b4a0ff', 'Bass': '#6edbb0', 'Drums': '#ffb66e'}[note.part], outline='')

    def close(self):
        self.stop(announce=False)
        self.root.destroy()


def main():
    root = tk.Tk()
    MusicApp(root)
    root.mainloop()
