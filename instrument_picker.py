"""Reusable category-filtered desktop instrument selection and SF2 import."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import soundbanks


class InstrumentPicker(ttk.Frame):
    def __init__(self, parent, part, variable, search):
        super().__init__(parent)
        self.part, self.variable, self.search = part, variable, search
        self.family = tk.StringVar(value='All types')
        ttk.Label(self, text=part).pack(anchor='w', pady=(0, 4))
        self.filter = ttk.Combobox(self, textvariable=self.family, state='readonly', height=16)
        self.filter.pack(fill='x', pady=(0, 4))
        self.box = ttk.Combobox(self, textvariable=variable, state='readonly', height=16)
        self.box.pack(fill='x')
        self.family.trace_add('write', self.refresh)
        self.search.trace_add('write', self.refresh)
        self.refresh()

    def refresh(self, *_):
        groups = soundbanks.groups(self.part == 'Drums')
        self.filter.configure(values=('All types', *groups))
        query = self.search.get().casefold().strip()
        names = [name for group, values in groups.items() for name in values
                 if self.family.get() in ('All types', group) and query in name.casefold()]
        self.box.configure(values=(*names, 'Mute'))


def import_dialog(app):
    path = filedialog.askopenfilename(parent=app.root, title='Import an instrument library',
                                     filetypes=[('SoundFont instruments', '*.sf2')])
    if not path:
        return
    dialog = tk.Toplevel(app.root)
    dialog.title('Import SoundFont instruments')
    dialog.transient(app.root)
    dialog.grab_set()
    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Instrument type (used for filtering and playing style)').pack(anchor='w')
    family = tk.StringVar(value='Auto')
    ttk.Combobox(frame, textvariable=family, state='readonly', values=('Auto', *soundbanks.FAMILIES), width=40).pack(fill='x', pady=10)
    ttk.Label(frame, text='Local SF2 files up to 64 MB. The app copies the library so it remains available.').pack(anchor='w')

    def commit():
        try:
            entry = soundbanks.import_file(path, family.get())
            for picker in app.instrument_pickers:
                picker.refresh()
            app.status.set(f"Imported {entry['name']}: {len(entry['presets'])} instruments. Choose them from the type filters.")
            dialog.destroy()
        except Exception as error:
            messagebox.showerror('Instrument import failed', str(error), parent=dialog)
    ttk.Button(frame, text='Import instruments', command=commit).pack(anchor='e', pady=(12, 0))

