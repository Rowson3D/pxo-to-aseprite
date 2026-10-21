"""Drop Pixelorama .pxo files (or folders of them) on this window to convert
them to Aseprite .aseprite files. Double-click to open it, or drop files on
its icon. The conversion and its checks are pxo_to_aseprite.py's.

Drag and drop needs tkinterdnd2 (py -m pip install --user tkinterdnd2);
without it the Add buttons still work.
"""
import json
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pxo_to_aseprite as conv  # noqa: E402

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TkinterDnD = None

SETTINGS = os.path.join(os.path.expanduser('~'), '.pxo_to_aseprite.json')

# Ash and Ember: warm charcoal, bone, one ember accent.
CHARCOAL, PANEL, LINE = '#28241f', '#332e28', '#4a423a'
BONE, DIM, EMBER = '#e6dccb', '#a39a8b', '#e0742c'
OK, BAD = '#9fbf7a', '#e0614f'


def load_settings():
    try:
        with open(SETTINGS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(values):
    try:
        with open(SETTINGS, 'w') as f:
            json.dump(values, f)
    except OSError:
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.jobs = queue.Queue()
        self.events = queue.Queue()
        self.busy = False
        settings = load_settings()

        root.title('pxo to Aseprite')
        root.configure(bg=CHARCOAL)
        root.geometry('560x420')
        root.minsize(420, 320)

        self.drop = tk.Label(root, text='Drop .pxo files or folders here', bg=PANEL, fg=BONE,
                             font=('Segoe UI', 13), relief='flat', bd=0, highlightthickness=2,
                             highlightbackground=LINE, height=4)
        self.drop.pack(fill='x', padx=16, pady=(16, 8))
        if TkinterDnD is not None:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind('<<DropEnter>>', lambda e: self.drop.config(highlightbackground=EMBER) or e.action)
            self.drop.dnd_bind('<<DropLeave>>', lambda e: self.drop.config(highlightbackground=LINE) or e.action)
            self.drop.dnd_bind('<<Drop>>', self.on_drop)
        else:
            self.drop.config(text='Drag and drop needs tkinterdnd2:\npy -m pip install --user tkinterdnd2', fg=DIM)

        buttons = tk.Frame(root, bg=CHARCOAL)
        buttons.pack(fill='x', padx=16)
        self.button(buttons, 'Add files', self.add_files).pack(side='left')
        self.button(buttons, 'Add folder', self.add_folder).pack(side='left', padx=8)

        out = tk.Frame(root, bg=CHARCOAL)
        out.pack(fill='x', padx=16, pady=(12, 0))
        tk.Label(out, text='Save to', bg=CHARCOAL, fg=DIM, font=('Segoe UI', 10)).pack(side='left')
        self.out_dir = tk.StringVar(value=settings.get('out_dir', ''))
        tk.Entry(out, textvariable=self.out_dir, bg=PANEL, fg=BONE, insertbackground=BONE, relief='flat',
                 font=('Segoe UI', 10), highlightthickness=1, highlightbackground=LINE,
                 highlightcolor=EMBER).pack(side='left', fill='x', expand=True, padx=8, ipady=3)
        self.button(out, 'Browse', self.pick_out).pack(side='left')
        tk.Label(root, text='Leave empty to save each one beside its .pxo.', bg=CHARCOAL, fg=DIM,
                 font=('Segoe UI', 9)).pack(anchor='w', padx=16)

        self.force = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text='Replace .aseprite files saved later than their .pxo', variable=self.force,
                       bg=CHARCOAL, fg=BONE, selectcolor=PANEL, activebackground=CHARCOAL,
                       activeforeground=BONE, font=('Segoe UI', 10)).pack(anchor='w', padx=12, pady=(6, 0))

        self.log = tk.Text(root, bg=PANEL, fg=BONE, relief='flat', font=('Consolas', 9), height=8,
                           highlightthickness=0, wrap='word', state='disabled')
        self.log.pack(fill='both', expand=True, padx=16, pady=(8, 16))
        for tag, colour in (('ok', OK), ('bad', BAD), ('dim', DIM)):
            self.log.tag_config(tag, foreground=colour)

        root.protocol('WM_DELETE_WINDOW', self.close)
        threading.Thread(target=self.worker, daemon=True).start()
        root.after(100, self.pump)

    def button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=LINE, fg=BONE, activebackground=EMBER,
                         activeforeground=CHARCOAL, relief='flat', font=('Segoe UI', 10), padx=10, pady=3,
                         cursor='hand2')

    def write(self, text, tag=None):
        self.log.config(state='normal')
        self.log.insert('end', text + '\n', tag)
        self.log.see('end')
        self.log.config(state='disabled')

    def on_drop(self, event):
        self.drop.config(highlightbackground=LINE)
        self.queue(self.root.tk.splitlist(event.data))
        return event.action

    def add_files(self):
        self.queue(filedialog.askopenfilenames(title='Pixelorama files',
                                               filetypes=[('Pixelorama', '*.pxo'), ('All files', '*.*')]))

    def add_folder(self):
        folder = filedialog.askdirectory(title='Folder of .pxo files')
        if folder:
            self.queue([folder])

    def pick_out(self):
        folder = filedialog.askdirectory(title='Save .aseprite files to')
        if folder:
            self.out_dir.set(folder)

    def queue(self, paths):
        files = conv.targets(list(paths), recurse=True)
        if paths and not files:
            self.write('No .pxo files in what was dropped.', 'dim')
        out_dir = self.out_dir.get().strip() or None
        for path in files:
            self.jobs.put((os.path.normpath(path), out_dir, self.force.get()))

    def worker(self):
        while True:
            path, out_dir, force = self.jobs.get()
            name = os.path.basename(path)
            try:
                if not force and conv.is_newer(conv.out_path_for(path, out_dir), path):
                    self.events.put(('dim', '%s kept: its .aseprite is newer' % name))
                    continue
                out, problems = conv.convert(path, out_dir)
                if problems:
                    self.events.put(('bad', '%s did not convert cleanly:' % name))
                    for p in problems:
                        self.events.put(('bad', '    ' + p))
                else:
                    self.events.put(('ok', '%s  ->  %s' % (name, os.path.join(os.path.basename(os.path.dirname(out)), os.path.basename(out)))))
            except Exception as e:  # noqa: BLE001 - shown in the log, the window keeps going
                self.events.put(('bad', '%s: %s' % (name, e)))

    def pump(self):
        while True:
            try:
                tag, text = self.events.get_nowait()
            except queue.Empty:
                break
            self.write(text, tag)
        self.root.after(100, self.pump)

    def close(self):
        save_settings({'out_dir': self.out_dir.get().strip()})
        self.root.destroy()


def main():
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    app = App(root)
    if len(sys.argv) > 1:
        app.queue(sys.argv[1:])
    root.mainloop()


if __name__ == '__main__':
    main()
