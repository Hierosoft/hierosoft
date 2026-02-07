# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(MODULE_DIR)
    sys.path.insert(0, REPO_DIR)

from hierosoft.hierosoftupdateframetkbase import HierosoftUpdateFrameTkBase
from hierosoft.moreweb.hierosoftupdate import HierosoftUpdate
import tkinter as tk
from tkinter import ttk


class HierosoftUpdateFrameTk(HierosoftUpdateFrameTkBase, HierosoftUpdate):
    def __init__(self, parent):
        HierosoftUpdateFrameTkBase.__init__(self, parent)
        # HierosoftUpdate.__init__(self, *args, **kwargs)
        # Assuming 'self.m_notebook' is the name from the base class
        # Hide tab (only works for Notebook with custom style):
        self.style = ttk.Style(self)
        self.style.layout("Hidden.TNotebook", [("Hidden.TNotebook.client", {"sticky": "nswe"})])
        self.style.layout("Hidden.TNotebook.Tab", [])
        self.m_notebook.configure(style="Hidden.TNotebook")
        self.m_notebook.select(self.m_packagesTabPanel)  # Select the page you want displayed


def main():
    root = tk.Tk()  # Create the root window
    frame = HierosoftUpdateFrameTk(root)  # Instantiate the frame with root as parent
    frame.pack(fill="both", expand=True)  # Pack the frame to fill the root
    root.after(0, frame.start)
    root.mainloop()  # Start the main event loop
    return 0


if __name__ == "__main__":
    sys.exit(main())
