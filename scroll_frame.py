"""A scrollable form that keeps growing controls accessible on smaller screens."""
import tkinter as tk
from tkinter import ttk


class ScrollablePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self, highlightthickness=0, background='#f2f4f8')
        bar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        self.body = ttk.Frame(canvas, padding=24)
        window = canvas.create_window(0, 0, window=self.body, anchor='nw')
        self.body.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))

        def wheel(event):
            if isinstance(event.widget, (ttk.Combobox, tk.Listbox, ttk.Spinbox)):
                return
            widget = event.widget
            while widget is not None:
                if widget is self.body:
                    canvas.yview_scroll(-int(event.delta / 120), 'units')
                    break
                widget = getattr(widget, 'master', None)
        canvas.bind_all('<MouseWheel>', wheel, add='+')
