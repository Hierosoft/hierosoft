#!/usr/bin/env python
import sys
import os
import subprocess
import shlex
import threading
import time

if sys.version_info.major >= 3:
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
    from tkinter import messagebox
else:
    # Python 2
    FileNotFoundError = IOError
    ModuleNotFoundError = ImportError
    NotADirectoryError = OSError
    import Tkinter as tk
    import tkFont
    import ttk
    import tkMessageBox as messagebox


def echo0(*args):
    print(*args, file=sys.stderr)


class MainForm(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.run_parts = None
        self.parent = parent
        self.parent.title('')
        self.parent.geometry("400x400")
        # self.label = tk.Label(text="Hello, world")
        # self.label.pack(padx=10, pady=10)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.read_delay = 1

    def set_startup_program(self, cmd):
        # self.thread = threading.Thread(target=self._set_startup_program, args=(cmd,))
        # self.thread.start()
        self.run_parts = cmd
        self.parent.after(self.read_delay, self._run_startup_program)

    def _run_startup_program(self):
        self._set_startup_program(self.run_parts)

    def _check_startup_program(self):
        raw_line = self.proc.stdout.readline()
        code = self.proc.poll()
        time.sleep(.5)
        echo0("[_check_startup_program] reading...")
        if raw_line == '' and code is not None:
            echo0("[_check_startup_program] done reading.")
            self.proc.stdout.close()
            echo0("[_check_startup_program] closed.")
            self.proc.wait()
            echo0("[_check_startup_program] done running.")
            return
        if raw_line:
            line = raw_line.strip()
            print("[_check_startup_program] read: ", line.strip(), flush=True)
            # echo0("[_set_startup_program] read: {}".format(line))
            self.listbox.insert(tk.END, line)

        self.parent.after(self.read_delay, self._check_startup_program)


    def _set_startup_program(self, cmd):
        self.run_parts = cmd
        if cmd is None:
            self.listbox.insert(
                tk.END,
                "cmd is None: There was no program specified."
            )
            return False
        if len(cmd) < 1:
            self.listbox.insert(tk.END, "There was no program specified.")
            return False
        py_cmd = None
        if cmd[0].lower().endswith("py") or cmd[0].lower().endswith("pyw"):
            py_cmd = ["/usr/bin/python3"] + cmd
        # "In Python 3.8, open() emits RuntimeWarning if buffering=1 for binary mode.
        # Because we never write to this file, pass 0 to switch buffering off."
        # ^ See <https://github.com/benoitc/gunicorn/pull/2146/files>
        #   found via <https://askubuntu.com/a/1216809>.

        # Just hangs:
        '''
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            # bufsize=1,  # bufsize isn't supported in binary mode
        )
        echo0("[_set_startup_program] reading...")
        # See <https://stackoverflow.com/a/6414278>:
        for raw_line in iter(proc.stdout.readline, b''):
            line = raw_line.strip()
            echo0(line)
            self.listbox.insert(tk.END, line)
        '''
        ls_cmd = ["/usr/bin/ls", "/home/owner/git/amcaw"]
        # cmd = py_cmd
        cmd = ls_cmd
        echo0("[_set_startup_program] Running: {}".format(shlex.join(cmd)))
        title = cmd[0]
        if ("python" in title) and (len(cmd) > 1):
            title = cmd[1]
        self.parent.title(title)
        echo0("title={}".format(title))
        self.run_parts = cmd
        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            # shell=True,
            encoding='utf-8',
            errors='replace',
            universal_newlines=True,
        )

        echo0("[_set_startup_program] reading...")
        self.parent.after(self.read_delay, self._check_startup_program)
        return True


if __name__ == "__main__":
    root = tk.Tk()
    mainform = MainForm(root)
    run_parts = []
    # sys.argv[1:]
    file_name = os.path.basename(__file__)
    for argi in range(1, len(sys.argv)):
        if file_name in sys.argv[argi]:
            run_parts = sys.argv[argi+1:]
            break
        run_parts.append(sys.argv[argi])
    mainform.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    mainform.set_startup_program(run_parts)
    echo0("mainloop is starting.")
    root.mainloop()
    echo0("mainloop is over.")
