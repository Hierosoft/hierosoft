# -*- coding: utf-8 -*-
'''
Provide a configured updater window.

Usage:

from hierosoft.gui_tk import show_update_window
options = {}
# set options
show_update_window(options)
# returns: 0 if ok, 1 if no UI

Options:

'''
from __future__ import print_function
import sys
import os
# import shutil
import threading
# import tarfile
# import zipfile
# import platform
import copy
# import time

from pprint import pformat

if sys.version_info.major >= 3:  # try:
    from tkinter import messagebox
    from tkinter import filedialog
    from tkinter import simpledialog
    # ^ such as name = simpledialog.askstring('Name', 'What is your name?')
    import tkinter as tk
    from tkinter import font
    from tkinter import ttk
    # from tkinter import tix
else:  # except ImportError:
    # Python 2
    import tkMessageBox as messagebox  # noqa F401,N813
    import tkFileDialog as filedialog  # noqa F401,N813
    import tkSimpleDialog as simpledialog  # noqa F401,N813
    import Tkinter as tk  # noqa F401,N813
    import tkFont as font  # noqa F401,N813
    import ttk
    # import Tix as tix

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
if __name__ == "__main__":
    if os.path.isfile(os.path.join(REPO_DIR, "hierosoft", "__init__.py")):
        sys.path.insert(0, REPO_DIR)  # find hierosoft if running gui_tk.py

# Dependencies are ok since:
# - On Windows, PowerShell script can install Python & run moreweb to get repo
# - On Linux, a shortcut can include bash commands to install Python & repo

import hierosoft  # noqa E402
from hierosoft import (  # noqa E402
    echo0,
    echo1,
    echo2,
    ASSETS_DIR,
    resource_add_path,
    resource_find,
    get_file_names,
    get_subdir_names,
    get_installed_bin,
)

THEME_DIR = os.path.join(ASSETS_DIR, "Forest-ttk-theme")
resource_add_path(THEME_DIR)

# from hierosoft.morelogging import (
#     view_traceback,
# )
from hierosoft.moreplatform import (  # noqa E402
    make_shortcut,
    install_archive,
)
from hierosoft.moreweb import (  # noqa E402
    # name_from_url,
    STATUS_DONE,
)

from hierosoft.moreweb.hierosoftupdate import HierosoftUpdate  # noqa E402

from hierosoft.moreweb.downloadmanager import DownloadManager  # noqa E402

from hierosoft.morelogging import (  # noqa E402
    view_traceback,
)

from hierosoft.ggrep import (  # noqa E402
    contains_any,
)

from hierosoft.hierosoftpacked import (  # noqa E402
    hierosoft_16px_png,
)


# from hierosoft.hierosoftlaunchertk import (  # noqa E402
#     HierosoftLauncherTk,
# )

# formerly part of blendernightly update.pyw:


class HierosoftUpdateFrame(HierosoftUpdate, ttk.Frame):
    """The updater only

    BlenderNightly should use this one.

    Args:
        root (tk.Tk): The actual tk root
        parent: root, or a frame of any kind.
    """

    @classmethod
    def get_help(cls, key):
        if key in DownloadManager.get_option_keys():
            return DownloadManager.get_help(key)
        return cls.HELP.get(key)

    def addRow(self, widget, *args, **kwargs):
        prefix = "[addRow] "
        self.auto_column = 0
        combined_kwargs = copy.deepcopy(self.widget_kwargs)
        for key, value in kwargs.items():
            if key in combined_kwargs:
                echo0(prefix+"Warning: specified %s=%s overrides %s"
                      % (key, value, combined_kwargs[key]))
            combined_kwargs[key] = value
        widget.grid(
            *args,
            row=self.auto_row,
            column=self.auto_column,
            **combined_kwargs,
        )
        self.auto_row += 1

    def addField(self, widget, *args, **kwargs):
        widget.grid(
            *args,
            row=self.auto_row,
            column=self.auto_column,
            **self.widget_kwargs,
            **kwargs,
        )
        self.auto_column += 1

    def __init__(self, parent, root, options, *args, **kwargs):
        # docstring is in class (in Sphinx it can only be here/there not both)
        # This region exists since the d_done code now contains the
        #   download code that was formerly synchronous and occurred
        #   after the synchronous download function ended.
        # TODO: Move this whole region to the event?
        HierosoftUpdate.__init__(self, parent, root, options)
        # ^ calls self.mgr.set_options which calls mgr.parser.set_options
        if root is None:
            raise ValueError("root must be non-None and must be `tk.Tk()`")
        if parent is None:
            raise ValueError(
                "parent must be non-None and can be root (tk.Tk()) or a frame"
            )
        self.root = root
        self.parent = parent  # not root if inside something else
        self._super(parent, *args, **kwargs)

        self.columnconfigure(index=0, weight=1)
        self.columnconfigure(index=1, weight=1)
        self.columnconfigure(index=2, weight=1)
        # self.rowconfigure(index=0, weight=1)
        # self.rowconfigure(index=1, weight=1)
        # self.rowconfigure(index=2, weight=1)
        # ^ weight=0 ensures widget isn't less than its own specified size
        photo = tk.PhotoImage(
            # data=transparent_png,
            # data=hierosoft_16px_png,
            data=hierosoft_16px_png,
        )
        root.iconphoto(False, photo)

        self.root.geometry("1000x600")
        self.root.minsize(600, 400)

        title_s = options.get('title')
        if title_s is None:
            title_s = "Hierosoft Launcher"
        self.root.title(title_s)
        self.root.wm_title(title_s)
        self.parent = parent

        # Formerly global:
        self.thread1 = None
        self.shown_progress = 0
        self.widget_kwargs = {
            'padx': 5,
            'pady': 10,
            'sticky': "nsew",
        }

        # Formerly before functions (which are now methods):

        base_height = 300
        self.root.geometry('300x' + str(base_height))
        # self.option_entries['']
        self.version_e = None
        self.del_arc_var = tk.IntVar()

        # ^ contains self.mgr.profile_path

        # Formerly before main:
        self.version_e = ttk.Entry(self.root)
        self.addRow(self.version_e)

        self.pflag_e = ttk.Entry(self.root)
        self.addRow(self.pflag_e)

        self.arch_e = ttk.Entry(self.root)
        self.addRow(self.arch_e)

        self.refresh_btn = ttk.Button(self.root, text="Refresh",
                                      command=self.refresh_click)
        self.addRow(self.refresh_btn, sticky='we')
        # ^ sticky='we' is like pack with fill='w'

        self.pbar = ttk.Progressbar(self.root)
        # orient="horizontal", length=200, mode="determinate"
        self.addRow(self.pbar, sticky='we')

        self.count_label = ttk.Label(self.root, text="")  # at bottom
        self.addRow(self.count_label, sticky='we')

        news = options.get('news')
        if news:
            for article in news:
                news_date_str = article.get('date')
                news_text = article.get('text')
                news_url = article.get('url')
                if news_date_str:
                    label = ttk.Label(self.root, text=news_date_str)
                    self.addRow(label, sticky="we")
                if news_text:
                    label = ttk.Label(self.root, text=news_text)
                    self.addRow(label, sticky="we")
                if news_url:
                    import webbrowser
                    button = ttk.Button(
                        self.root,
                        text=news_text,
                        command=lambda url=news_url: webbrowser.open(
                            url,
                            new=0,
                            autoraise=True,
                        )
                    )
                    self.addRow(button, sticky="we")

        self.del_arc_cb = ttk.Checkbutton(
            self.root, text="Delete archive after install",
            variable=self.del_arc_var,
        )
        # self.addRow(self.del_arc_cb, sticky='we')  # not implemented

    def _super(self, parent, *args, **kwargs):
        """Overridable super-like method (initialize the superclass; required)
        """
        ttk.Frame.__init__(self, parent, *args, **kwargs)

    def push_label(self, s):
        new_label = ttk.Label(self.root, text=s)
        self.addRow(new_label, pady=0)
        self.msg_labels.append(new_label)
        self.root.update()

    def uninstall_click(self, meta):
        print("* uninstalling {}".format(meta))
        # make_shortcut(meta, "blender", self.mgr, push_label=self.push_label,
        #               uninstall=True)
        self.d_click(meta, uninstall=True)

    def remove_ar_click(self, meta):
        print("* uninstalling {}".format(meta))
        # make_shortcut(meta, "blender", self.mgr, push_label=self.push_label,
        #               uninstall=True)
        self.d_click(meta, uninstall=False, remove_download=True)

    def _d_progress(self, evt):
        """This should only be called by _process_events
        on the main thread (other threads will throw access violation
        trying to access the GUI).

        For the generic event handler, use self.d_progress from superclass
        instead (to append an event to the event queue).
        """
        if evt['loaded'] - self.shown_progress > 1000000:
            self.shown_progress = evt['loaded']
            self.pbar['value'] = evt['loaded']
            # print(evt['loaded'])
            # evt['total'] is not implemented
            self.count_label.config(
                text="downloading...{}MB.".format(int(evt['loaded']/1024/1024))
            )
        if evt.get('status') == STATUS_DONE:
            echo0("Warning: Got status={} for progress."
                  " Set cb_done to something else and ensure"
                  " the process is programmed to call cb_done"
                  "".format(STATUS_DONE))
        self.root.update()

    # There is a generic _d_done on superclass called _on_archive_ready
    # but if not not installing an archive, set cb_done to something useful
    # (such as, install Hierosoft after Python is installed by download_first)

    def settings_to_fields(self):
        """Put relevant option values into GUI fields.

        This overrides the superclass method which is a placeholder.
        """
        # formerly set_entries
        prefix = "[HierosoftUpdateFrame settings_to_fields] "
        if self.mgr.parser is None:
            echo0(prefix+'INFO: self.mgr.parser is None')
            return
        version = self.mgr.parser.get_option('version')
        _platform = self.mgr.parser.get_option('platform')
        arch = self.mgr.parser.get_option('arch')
        if self.version_e is None:
            raise RuntimeError(
                "Error: self.version_e is None."
                " The GUI must be set up before calling settings_to_fields,"
                " because the GUI elements are used as the data source"
                " directly later."
            )
        if version is not None:
            self.version_e.delete(0, tk.END)
            self.version_e.insert(0, version)
        if _platform is not None:
            self.pflag_e.delete(0, tk.END)
            self.pflag_e.insert(0, _platform)
        if arch is not None:
            self.arch_e.delete(0, tk.END)
            self.arch_e.insert(0, arch)

    def fields_to_settings(self):
        """Override superclass: load variables from GUI
        """
        # formerly load_user_settings
        keyfields = {
            "version": self.version_e,  # key used by only_v property
            "arch": self.arch_e,  # key used by only_a property
            "platform": self.pflag_e,  # key used by only_p property
        }
        for key, field in keyfields.items():
            value = field.get().strip()
            if len(value) == 0:
                value = None
            elif key == "arch":
                if " " in value:
                    # space-separated values
                    value = value.split()
            keyfields[key] = value
        self.set_all_options(keyfields, False)

    def refresh_ui(self):
        # prefix = "[refresh_ui] "
        # self.settings_to_fields()
        for label in self.msg_labels:
            label.grid_remove()
        for btn in self.dl_buttons:
            btn.grid_remove()

        self.fields_to_settings()

        # region override superclass values from options
        #   (Update options to whatever the user sees/changed in the GUI)
        self.count_label.config(text="scraping Downloads page...")
        self.root.update()
        # ^ normally only_* are set by set_options in superclass
        # endregion override superclass values from options

        self._download_page()
        status_s = self.v_msg + "count: " + str(len(self.a_urls))
        self.count_label.config(text=status_s)
        self.root.update()
        print("  matched "+str(len(self.a_urls))+" "+self.a_msg+"url(s)")

        row = 1
        url_installed_count = 0
        for meta in self.link_metas + self.installed_metas:
            # see https://stackoverflow.com/questions/17677649/\
            # tkinter-assign-button-command-in-loop-with-lambda
            user_button = ttk.Button(
                self.root,
                text="Install "+meta['luid'],
                command=lambda meta=meta: self.d_click(meta)
            )

            meta['button'] = user_button

            uninstall_caption = "Uninstall"
            if meta.get('installed') is True:
                uninstall_caption = "Remove old"
            else:
                self.dl_buttons.append(user_button)
                self.addRow(user_button)  # row=row, column=0
            uninstall_button = ttk.Button(
                self.root,
                text=uninstall_caption+" "+meta['luid'],
                command=lambda meta=meta: self.uninstall_click(meta)
            )
            meta['uninstall_button'] = uninstall_button
            bin_path = get_installed_bin(
                self.versions_path,
                meta['luid'],
                self.bin_names,
            )
            if bin_path is not None:
                meta['Exec'] = bin_path
                user_button.config(state=tk.DISABLED)
                if os.path.isfile(bin_path):
                    self.dl_buttons.append(uninstall_button)
                    self.addRow(uninstall_button)
                # else:
                #     uninstall_button.config(state=tk.DISABLED)
                url_installed_count += 1
            else:
                print("The bin path is unknown for {}".format(meta))
            row += 1
        if url_installed_count > 0:
            self.push_label("(already installed {} above)"
                            "".format(url_installed_count))
        else:
            echo0("no available downloads are installed into {} yet."
                  "".format(self.versions_path))
        if self.dl_but_not_inst_count > 0:
            self.push_label("Downloaded but not installed ({}):"
                            "".format(self.dl_but_not_inst_count))
        for meta in self.dl_metas:
            # see https://stackoverflow.com/questions/17677649/\
            # tkinter-assign-button-command-in-loop-with-lambda
            if meta.get('Exec') is None:
                if meta['luid'] in (meta['luid'] for meta in self.link_metas):
                    # already is a button
                    continue
                # print("  # not installed: " + meta['filename'])
                user_button = ttk.Button(
                    self.root,
                    text="Install "+meta['luid'],
                    command=lambda meta=meta: self.d_click(meta)
                )
                meta['button'] = user_button
                self.dl_buttons.append(user_button)
                self.addRow(user_button)

                if meta['luid'] in (meta['luid'] for meta in self.link_metas):
                    # already is a button
                    continue
                # print("  # not installed: " + meta['filename'])
                remove_button = ttk.Button(
                    self.root,
                    text="Delete "+meta['luid'],
                    command=lambda meta=meta: self.remove_ar_click(meta)
                )
                meta['button'] = remove_button
                self.dl_buttons.append(remove_button)
                self.addRow(remove_button)

                row += 1
            # else:
                # print("  # installed: " + meta['filename'])

        self.thread1 = None
        # self.addRow(self.refrech_btn, sticky="we")
        # self.refresh_btn.config(fg='black')
        self.refresh_btn.config(state=tk.NORMAL)
        expand = 0
        old_bottom = (
            self.count_label.winfo_y()
            + self.count_label.winfo_height()
        )
        # if len(self.dl_buttons) > 2:
        self.root.update()
        # use max heights to resize window,
        # since widget height is 0 if crushed by window:
        btn_h_max = self.refresh_btn.winfo_height()
        label_h_max = self.count_label.winfo_height()
        for i in range(0, len(self.dl_buttons)):
            if self.dl_buttons[i].winfo_height() > btn_h_max:
                btn_h_max = self.dl_buttons[i].winfo_height()
            expand += btn_h_max
        for i in range(0, len(self.msg_labels)):
            if self.msg_labels[i].winfo_height() > label_h_max:
                label_h_max = self.msg_labels[i].winfo_height()
            expand += label_h_max
        if expand > 0:
            print("expand: " + str(expand))
            # self.root.config(height=self.root.winfo_width()+expand)
            self.root.geometry('400x' + str(old_bottom+expand))

    def start_refresh(self):
        """Start the refresh thread that will download and parse the page.

        Requires: self.mgr.parser to be set.
        """
        # self.refresh_btn.grid_remove()
        # self.refresh_btn.config(fg='gray')
        # self.refresh_ui()
        prefix = "[start_refresh] "
        if self.thread1 is None:
            echo0("")
            echo0(prefix+"Starting refresh thread...")
            self.thread1 = threading.Thread(target=self.refresh_ui, args=())
            self.refresh_btn.config(state=tk.DISABLED)
            self.root.update()
            self.thread1.start()
        else:
            echo0("WARNING: Refresh is already running.")

    def refresh_click(self):
        self.start_refresh()


root = None


def get_tk():
    global root
    if root is not None:
        return root

    try:
        root = tk.Tk()
    except tk.TclError:
        echo0("FATAL ERROR: Cannot use tkinter from terminal")
        return 1

    # region Forest-ttk-theme-example
    root.option_add("*tearOff", False)  # This is always a good idea

    root.columnconfigure(index=0, weight=1)
    root.rowconfigure(index=0, weight=1)

    # Create a style
    style = ttk.Style(root)

    theme_name = "forest-dark"
    themes_dir = resource_find(theme_name)

    # Import the tcl file
    tcl_theme_rel = "%s.tcl" % theme_name
    tcl_theme_path = resource_find(tcl_theme_rel)
    if not tcl_theme_path:
        raise FileNotFoundError(tcl_theme_rel)
    root.tk.call("source", tcl_theme_path)

    # Set the theme with the theme_use method
    root.tk.call('lappend', 'auto_path', themes_dir)  # necessary if not in CWD
    # root.tk.call('package', 'require', theme_name)
    style.theme_use(theme_name)

    # endregion Forest-ttk-theme-example
    return root


def show_update_window(options):
    root = get_tk()
    option_keys = HierosoftUpdateFrame.get_option_keys()
    for key in option_keys:
        if key not in option_keys:
            raise ValueError("{} is not a valid option.".format(key))
    parent = root  # allowed to be a container instead of root
    app = HierosoftUpdateFrame(parent, root, options)
    # app.pack(side="top", fill="both", expand=True)
    app.grid(sticky="nsew")

    root.after(500, app.start_refresh)  # requires app.mgr.parser
    root.mainloop()
    return 0


def main():
    # Avoid "RuntimeError: main thread is not in main loop"
    # such as on self.count_label.config
    # (not having a separate main function may help).
    options = {}
    options['title'] = "Hierosoft Launcher"
    key = None
    # option_keys = HierosoftUpdateFrame.get_option_keys()
    if len(sys.argv) >= 3:
        for argI in range(len(sys.argv)):
            arg = sys.argv[argI]
            if key is not None:
                options[key] = arg
                key = None
            elif arg.startswith("--"):
                if arg in ["--verbose", "--debug"]:
                    # already handled by __init__.py
                    pass
                else:
                    key = arg[2:]

    return show_update_window(options)


if __name__ == "__main__":
    sys.exit(main())
