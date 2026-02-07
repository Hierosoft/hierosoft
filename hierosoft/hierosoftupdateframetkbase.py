# -*- coding: utf-8 -*-

import gettext
import tkinter as tk
from tkinter import ttk

_ = gettext.gettext

class HierosoftUpdateFrameTkBase(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.parent.title("")
        self.parent.geometry("723x398")

        self.m_outerHeaderPanel = ttk.Frame(self)
        self.m_outerHeaderPanel.pack(fill="x", expand=False, padx=0, pady=0)

        self.m_notebook = ttk.Notebook(self)
        self.m_notebook.pack(fill="both", expand=True, padx=0, pady=0)

        self.m_packagesTabPanel = ttk.Frame(self.m_notebook)
        self.m_notebook.add(self.m_packagesTabPanel, text=_("Packages"))

        self.m_packagesSplitter = ttk.PanedWindow(self.m_packagesTabPanel, orient="horizontal")
        self.m_packagesSplitter.pack(fill="both", expand=True)

        self.m_packagesPanel = ttk.Frame(self.m_packagesSplitter)
        self.m_packagePanel = ttk.Frame(self.m_packagesSplitter)

        self.m_packagesSplitter.add(self.m_packagesPanel)
        self.m_packagesSplitter.add(self.m_packagePanel)

        self.m_packagesTabPanel.after_idle(lambda: self.m_packagesSplitter.sashpos(0, 229))

        # Setup for m_packagesPanel
        self.m_scrolledWindow1 = tk.Canvas(self.m_packagesPanel)
        self.vbar1 = ttk.Scrollbar(self.m_packagesPanel, orient="vertical", command=self.m_scrolledWindow1.yview)
        self.hbar1 = ttk.Scrollbar(self.m_packagesPanel, orient="horizontal", command=self.m_scrolledWindow1.xview)
        self.m_scrolledWindow1.configure(yscrollcommand=self.vbar1.set, xscrollcommand=self.hbar1.set)

        self.m_scrolledWindow1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.vbar1.grid(row=0, column=1, sticky="ns", padx=0, pady=5)
        self.hbar1.grid(row=1, column=0, sticky="ew", padx=5, pady=0)

        self.m_packagesPanel.grid_rowconfigure(0, weight=1)
        self.m_packagesPanel.grid_columnconfigure(0, weight=1)

        self.inner_frame1 = ttk.Frame(self.m_scrolledWindow1)
        self.m_scrolledWindow1.create_window(0, 0, anchor="nw", window=self.inner_frame1)

        def configure_inner1(event):
            self.m_scrolledWindow1.config(scrollregion=self.m_scrolledWindow1.bbox("all"))

        self.inner_frame1.bind("<Configure>", configure_inner1)

        # Setup for m_packagePanel
        self.m_scrolledWindow2 = tk.Canvas(self.m_packagePanel)
        self.vbar2 = ttk.Scrollbar(self.m_packagePanel, orient="vertical", command=self.m_scrolledWindow2.yview)
        self.hbar2 = ttk.Scrollbar(self.m_packagePanel, orient="horizontal", command=self.m_scrolledWindow2.xview)
        self.m_scrolledWindow2.configure(yscrollcommand=self.vbar2.set, xscrollcommand=self.hbar2.set)

        self.m_scrolledWindow2.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.vbar2.grid(row=0, column=1, sticky="ns", padx=0, pady=5)
        self.hbar2.grid(row=1, column=0, sticky="ew", padx=5, pady=0)

        self.m_packagePanel.grid_rowconfigure(0, weight=1)
        self.m_packagePanel.grid_columnconfigure(0, weight=1)

        self.inner_frame2 = ttk.Frame(self.m_scrolledWindow2)
        self.m_scrolledWindow2.create_window(0, 0, anchor="nw", window=self.inner_frame2)

        def configure_inner2(event):
            self.m_scrolledWindow2.config(scrollregion=self.m_scrolledWindow2.bbox("all"))

        self.inner_frame2.bind("<Configure>", configure_inner2)

        self.m_statusBar = ttk.Label(self, text="", relief="sunken", anchor="w")
        self.m_statusBar.pack(side="bottom", fill="x")
