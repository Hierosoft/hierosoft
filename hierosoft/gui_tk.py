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
import shutil
import threading
import tarfile
import zipfile
import platform
import copy
import time

if sys.version_info.major >= 3:  # try:
    from tkinter import messagebox
    from tkinter import filedialog
    import tkinter as tk
    import tkinter.font as tkFont
    from tkinter import ttk
    # from tkinter import tix
else:  # except ImportError:
    # Python 2
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
    import Tkinter as tk
    import tkFont
    import ttk
    # import Tix as tix

import hierosoft
from hierosoft import (
    echo0,
    echo1,
    echo2,
)

# from hierosoft.logging import (
#     view_traceback,
# )
from hierosoft.moreplatform import (
    make_shortcut,
)
from hierosoft.moreweb import (
    DownloadManager,
    name_from_url,
    STATUS_DONE,
)

from hierosoft.logging import (
    view_traceback,
)

from hierosoft.ggrep import (
    contains_any,
)

# formerly part of blendernightly update.pyw:


# TODO: use classes
class MainApplication(tk.Frame):

    HELP = {
        'title': "Set the window title for the updater.",
        'platforms': (
            "A dictionary of platforms where the key can be any"
            " platform.system() value such as Linux, Windows, or Darwin"
            " and the value of each is the substring in the filename"
            " for that platform. Example:"
            " platforms={'Linux':\"linux\", 'Windows':\"windows\","
            " 'Darwin':\"macos\"}. The only value of the"
            " current platform will be set as the entry box value used"
            " by the DownloadManager."
        ),
        'architectures': (
            "A dictionary of architectures where the key can be any"
            " platform.system() value such as Linux, Windows, or Darwin"
            " and the value of each is the substring in the filename"
            " for that platform. Example:"
            " platforms={'Linux':\"x64\", 'Windows':\"x64\","
            " 'Darwin':[\"x64\", \"arm64\"]}. The only value of the"
            " current platform will be set as the entry box value used"
            " by the DownloadManager."
        ),
    }

    @classmethod
    def get_option_keys(cls):
        return list(cls.HELP.keys()) + DownloadManager.get_option_keys()

    @classmethod
    def get_help(cls, key):
        if key in DownloadManager.get_option_keys():
            return DownloadManager.get_help(key)
        return HELP.get(key)

    def set_options(self, options):
        for key, value in options.items():
            if key in DownloadManager.get_option_keys():
                self.mgr.set_options({key: value})
            elif key == "platforms":
                self.mgr.set_options({'platform': value[platform.system()]})
            elif key == "architectures":
                self.mgr.set_options({'arch': value[platform.system()]})
        self.set_entries()

    def __init__(self, parent, options, *args, **kwargs):
        # region for d_done
        # This region exists since the d_done code now contains the
        #   download code that was formerly synchronous and occurred
        #   after the synchronous download function ended.
        # TODO: Move this whole region to the event?
        self.download_done = False
        self.archive_path = None
        self.enable_install = None
        self.remove_download = None
        self.bn_path = None
        self.archives_path = None
        self.versions_path = None
        self.installed_path = None  # TODO: track in meta instead?
        self.action = None
        self.uninstall = None  # TODO: move this to the event
        self.meta = None
        self.update_past_verb = None
        self.update_present_verb = None
        self.action_present_verb = None
        # region for d_done
        self.events = []


        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent

        self.root.geometry("1000x600")
        self.root.minsize(600, 400)

        key = None
        title_s = options.get('title')
        if title_s is None:
            title_s = "Hierosoft Update"
        self.root.title(title_s)
        self.root.wm_title(title_s)
        self.parent = parent

        # Formerly global:
        self.thread1 = None
        self.shown_progress = 0


        # Formerly before functions (which are now methods):

        base_height = 300
        self.root.geometry('300x' + str(base_height))
        self.urls = None
        self.count_label = None
        self.only_v = None
        self.only_a = None
        self.v_urls = None  # urls matching specified Blender version (tag)
        self.p_urls = None  # urls matching specified platform flag
        self.a_urls = None  # urls matching specified architecture
        self.option_entries = {}
        # self.option_entries['']
        self.version_e = None
        self.refresh_btn = None
        self.pbar = None
        self.del_arc_var = tk.IntVar()
        self.mgr = DownloadManager()
        # ^ contains self.mgr.profile_path
        self.dl_buttons = []
        self.msg_labels = []
        self.bin_names = ["blender", "blender.exe"]

        # Formerly before main:
        self.version_e = tk.Entry(self.root)
        self.version_e.pack()

        self.pflag_e = tk.Entry(self.root)
        self.pflag_e.pack()

        self.arch_e = tk.Entry(self.root)
        self.arch_e.pack()

        self.set_options(options)  # Does call self.mgr.set_options on match

        self.refresh_btn = tk.Button(self.root, text="Refresh",
                                     command=self.refresh_click)
        self.refresh_btn.pack(fill='x')

        self.pbar = ttk.Progressbar(self.root)
        # orient="horizontal", length=200, mode="determinate"
        self.pbar.pack(fill='x')

        self.count_label = tk.Label(self.root, text="")
        self.count_label.pack()

        self.del_arc_cb = tk.Checkbutton(self.root, text="Delete archive after install",
                                         variable=self.del_arc_var)
        # self.del_arc_cb.pack()  # not implemented

    def _process_events(self):
        '''
        Process each event dictionary in self.events and use the command
        to determine what to do. This occurs on the main thread such as
        in case the main thread is a GUI, which threads may not be
        able to access in some frameworks. Instead, threads should
        append events to self.events, and the main thread should poll
        the outcome of calls by calling this and checking for some state
        such as one that "d_done" (or the _d_done event) sets.

        Before adding an event to self.events, making a deepcopy is
        recommended (especially before adding 'command' where
        applicable).
        '''
        done_events = []
        while len(self.events) > 0:
            event = self.events[0]
            echo2("* processing {}".format(event))
            command = event.get('command')
            del self.events[0]
            if command is None:
                echo0("Error: command is one for event={}".format(event))
                continue
            elif command == "d_progress":
                self._d_progress(event)
                done_events.append(event)
            elif command == "d_done":
                self._d_done(event)
                done_events.append(event)
            else:
                echo0("Error: command '{}' is unknown for event={}"
                      "".format(command, event))

        return done_events

    def push_label(self, s):
        new_label = tk.Label(self.root, text=s)
        new_label.pack()
        self.msg_labels.append(new_label)
        self.root.update()

    def d_progress(self, evt):
        '''
        This doesn't have to run on the main thread (so don't access the
        GUI directly here).
        '''
        event = copy.deepcopy(evt)
        event['command'] = "d_progress"
        self.events.append(event)

    def _d_progress(self, evt):
        if evt['loaded'] - self.shown_progress > 1000000:
            self.shown_progress = evt['loaded']
            self.pbar['value'] = evt['loaded']
            # print(evt['loaded'])
            # evt['total'] is not implemented
            self.count_label.config(text="downloading..." +
                                    str(int(evt['loaded']/1024/1024)) + "MB..")
        if evt.get('status') == STATUS_DONE:
            echo0("Warning: Got {} for progress,"
                  " so progress was used but being redirected to _d_done."
                  "".format(STATUS_DONE))
            return self._d_done(self, evt)
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


    def d_click(self, meta, uninstall=False, remove_download=False):
        self.meta = meta
        self.remove_download = remove_download
        self.uninstall = uninstall
        self.update_past_verb = "Updated"
        self.update_present_verb = "Updating"
        self.action_present_verb = "Installing"
        self.action = "install"
        self.enable_install = True
        if uninstall:
            self.enable_install = False
            self.update_past_verb = "Removed"
            self.update_present_verb = "Removing"
            self.action_present_verb = "Uninstalling"
            self.action = "uninstall"
        if remove_download:
            self.enable_install = False
        for btn in self.dl_buttons:
            btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        self.download_clicked_btn = meta.get('button')
        uninstall_btn = meta.get("uninstall_button")
        if not uninstall:
            if self.download_clicked_btn is not None:
                self.download_clicked_btn.pack_forget()
        else:
            if remove_download:
                if self.download_clicked_btn is not None:
                    self.download_clicked_btn.pack_forget()
            if uninstall_btn is not None:
                uninstall_btn.pack_forget()

        self.root.update()
        self.shown_progress = 0
        print("")
        for label in self.msg_labels:
            label.pack_forget()
        print(self.action_present_verb + ":")
        print("  version: " + meta['version'])
        print("  commit: " + meta['commit'])
        self.pbar['maximum'] = 200*1024*1024  # TODO: get actual MB count
        self.pbar['value'] = 0
        url = meta.get('url')
        abs_url = None
        if url is not None:
            abs_url = self.mgr.absolute_url(url)

        dest_id = meta.get('id')
        if dest_id is None:
            dest_id = self.mgr.parser.id_from_name(meta['filename'],
                                                   remove_ext=True)
        # print("new_filename: " + self.mgr.parser.id_from_url(url))
        dl_name = meta.get('filename')  # name_from_url(url)
        user_downloads_path = self.mgr.get_downloads_path()
        self.bn_path = os.path.join(user_downloads_path, "blendernightly")
        self.archives_path = os.path.join(self.bn_path, "archives")
        if not os.path.isdir(self.archives_path):
            print("  creating: " + self.archives_path)
            os.makedirs(self.archives_path)
        self.versions_path = os.path.join(self.bn_path, "versions")
        self.installed_path = os.path.join(self.versions_path, dest_id)
        print("action={}: {}".format(self.action, self.installed_path))  # /2.??-<commit>
        self.archive_path = None
        if dl_name is not None:
            self.archive_path = os.path.join(self.archives_path, dl_name)
        if self.enable_install:
            found_count = 0
            total_count = 0
            for flag_name in self.bin_names:
                total_count += 1
                flag_path = os.path.join(self.installed_path, flag_name)
                if os.path.isfile(flag_path):
                    found_count += 1
                    msg = "Already installed " + meta['id'] + "."
                    print("  already_installed: true")
                    self.push_label(msg)
                    self.count_label.config(text=msg)
                    for btn in self.dl_buttons:
                        btn.config(state=tk.NORMAL)
                    self.refresh_btn.config(state=tk.NORMAL)
                    self.root.update()
                    return
            print("* done checking for {} binaries".format(total_count))

            if os.path.isfile(self.archive_path):
                self.push_label("Warning: Resuming with existing archive")
                self.push_label(self.archive_path)
                echo0('* archive_path="{}": {} is already done'
                      ''.format(self.archive_path, self.action))
                self._d_done({'status': STATUS_DONE})
                return

            # abs_url should never be None if file already exists
            print("  - downloading: " + abs_url)
            with open(self.archive_path, 'wb') as f:
                self.download_done = False
                self.mgr.download(f, abs_url,
                                  cb_progress=self.d_progress,
                                  cb_done=self.d_done)
                while not self.download_done:
                    # Keep the file open until the download completes
                    #   or fails.
                    # TODO: timeout
                    time.sleep(.25)
                    self._process_events()
        else:
            echo0("enable_install={}".format(self.enable_install))

    def d_done(self, evt):
        '''
        This doesn't have to run on the main thread (so don't access the
        GUI directly here).
        '''
        self.download_done = True
        event = copy.deepcopy(evt)
        event['command'] = "d_progress"
        self.events.append(event)

    def _d_done(self, evt):
        meta = self.meta
        archive_path = self.archive_path
        if self.download_done:
            echo0("Warning: download is already done.")
        self.download_done = True
        err = evt.get('error')
        if err is None:
            print("Download finished!")
        else:
            print("Download stopped due to: {}".format(err))
            return
        self.pbar['value'] = 0
        # self.root.update()

        tar = None
        ext = None
        fmt = None
        fmt_bad = False
        if archive_path is not None:
            ext = hierosoft.get_ext(archive_path)
            # if archive_path.lower()[-8:] == ".tar.bz2":
            if ext.lower() == "bz2":
                fmt = "r:bz2"
            elif ext.lower() == "gz":
                fmt = "r:gz"
            elif ext.lower() == "xz":
                fmt = "r:xz"
            elif ext.lower() == "zip":
                fmt = "zip"
            else:
                msg = ("ERROR: unknown file format for '" +
                       archive_path + "'")
                self.push_label("unknown format " + ext)
                print(msg)
        if self.enable_install:
            if fmt is not None:
                # try:
                if fmt != "zip":
                    tar = tarfile.open(archive_path, fmt)
                else:
                    tar = zipfile.ZipFile(archive_path)
                '''
                except:
                    fmt_bad = True
                    msg = "ERROR: archive not " + fmt
                    self.push_label(msg)
                    print(msg)
                '''
        if fmt_bad:
            os.remove(archive_path)
            msg = "  - deleting downloaded '" + archive_path + "'..."
            echo0(msg)
            self.push_label("Deleted bad download.")
            self.push_label("Download again.")
        if self.remove_download:
            msg = "  - deleting downloaded '" + archive_path + "'..."
            print(msg)
            os.remove(archive_path)
        else:
            if archive_path is not None:
                msg = "  - leaving downloaded '" + archive_path + "'..."
                print(msg)

        if tar is None:
            if self.enable_install:
                for btn in self.dl_buttons:
                    btn.config(state=tk.NORMAL)
                self.refresh_btn.config(state=tk.NORMAL)
                return
        else:
            print("  fmt: " + fmt)
        tmp_path = os.path.join(self.bn_path, "tmp")
        if self.enable_install:
            if not os.path.isdir(tmp_path):
                print("* created {}".format(tmp_path))
                os.makedirs(tmp_path)
        else:
            print("* tmp_path: {}".format(tmp_path))
        # for i in tar:
            # tar.extractfile(i)
        ok = False
        try:
            # if self.uninstall:
            #     msg = "examining archive..."
            if self.enable_install:
                msg = "extracting..."
                self.count_label.config(text=msg)
                self.root.update()
                # self.push_label(msg)
                print(msg)
                tar.extractall(tmp_path)
            ok = True
        except EOFError:
            msg = "ERROR: archive incomplete"
            self.push_label(msg)
            print(msg)
        finally:
            if tar is not None:
                tar.close()
                tar = None
        ext_path = tmp_path  # changes to sub if archive has only 1 dir
        if self.enable_install:
            msg = "checking tmp..."
            self.count_label.config(text=msg)
            self.root.update()
            # self.push_label(msg)
            print(msg)
            subdirs = hierosoft.get_subdir_names(tmp_path)

            if len(subdirs) == 1:
                ext_path = os.path.join(tmp_path, subdirs[0])
                print("  Detected tar-like (single-folder) archive using '"
                      + ext_path + "' as program root")
            elif len(subdirs) == 0:
                print("  Detected no extracted subdirectories...")
                files = hierosoft.get_file_names(tmp_path)
                if len(files) == 0:
                    print("    and found no files either, so failed.")
                    ok = False
                else:
                    print("    but found files, so using '" + ext_path +
                          "' as program root")
            else:
                print("  Detected windows-like (multi-folder) archive, used '" +
                      ext_path + "' as program root")
            if tar is not None:
                tar.close()
                tar = None

        if self.enable_install:
            msg = "moving from tmp..."
            # if self.uninstall:
            #     msg = "examining extracted tmp..."
            self.count_label.config(text=msg)
            self.root.update()
            # self.push_label(msg)
            print(msg)

        remove_tmp = False
        if not ok:
            remove_tmp = True
        if os.path.isdir(self.installed_path):
            # msg = "Already installed " + meta['id'] + "."
            meta['installed_bin'] = hierosoft.get_installed_bin(
                self.versions_path,
                meta['id'],
                self.bin_names,
            )
            if self.enable_install:
                if make_shortcut(meta, "blender", self.mgr, push_label=self.push_label,
                                 uninstall=self.uninstall):
                    msg = ("  - {} the old desktop shortcut"
                           "".format(self.update_past_verb))
                else:
                    msg = ("  - {} the old desktop shortcut failed."
                           "".format(self.update_present_verb))
                self.count_label.config(text=msg)
                self.root.update()
                remove_tmp = True
            else:
                make_shortcut(meta, "blender", self.mgr, push_label=self.push_label,
                              uninstall=self.uninstall)
        if remove_tmp:
            if os.path.isdir(tmp_path):
                print("  - deleting temporary '" + tmp_path + "'...")
                shutil.rmtree(tmp_path)
        if ok:
            try:
                if self.enable_install:
                    print("  - moving {} to {}".format(ext_path,
                                                       self.installed_path))
                    shutil.move(ext_path, self.installed_path)
                else:
                    if os.path.isdir(ext_path):
                        print("* WARNING: removing {}".format(ext_path))
                        shutil.rmtree(ext_path)
                    if os.path.isdir(self.installed_path):
                        print("* uninstalling {}".format(ext_path))
                        shutil.rmtree(self.installed_path)
                self.count_label.config(text=self.action+" is complete.")
                print("* {} is complete".format(self.action))
                if self.enable_install:
                    if self.download_clicked_btn is not None:
                        self.download_clicked_btn.pack_forget()
                        self.download_clicked_btn = None
                else:
                    if uninstall_btn is not None:
                        uninstall_btn.pack_forget()

                self.root.update()
                meta['installed_bin'] = hierosoft.get_installed_bin(
                    self.versions_path,
                    meta['id'],
                    self.bin_names,
                )
                if self.enable_install:
                    if make_shortcut(meta, "blender", self.mgr,
                                     push_label=self.push_label,
                                     uninstall=self.uninstall):
                        msg = ("{} the desktop shortcut"
                               "".format(self.update_past_verb))
                    else:
                        msg = ("{} the desktop shortcut failed."
                               "".format(self.update_present_verb))
                else:
                    make_shortcut(meta, "blender", self.mgr,
                                  push_label=self.push_label,
                                  uninstall=self.uninstall)
            except:
                msg = self.action + " could not finish moving"
                if self.uninstall:
                    msg = self.action + " could not finish deleting"
                self.push_label(msg)
                self.count_label.config(text="Installation failed.")
                self.root.update()
                self.push_label("to " + meta['id'])
                print("  from (extracted) '" + ext_path + "'")
                print(msg)
                print("  to '" + self.installed_path + "'")
                view_traceback()
        else:
            if archive_path is not None:
                msg = "  Deleting downloaded '" + archive_path + "'..."
                print(msg)
                self.push_label("Deleted bad download.")
                self.push_label("Download again.")
                os.remove(archive_path)

        for btn in self.dl_buttons:
            btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        self.root.update()
        self.meta = None

    def set_entries(self):
        if self.mgr.parser is None:
            echo0('[MainApplication set_entries] INFO: self.mgr.parser is None')
            return
        version = self.mgr.parser.get_option('version')
        platform = self.mgr.parser.get_option('platform')
        arch = self.mgr.parser.get_option('arch')
        if self.version_e is None:
            raise RuntimeError(
                "[MainApplication set_entries] Error: self.version_e is None."
                " The GUI must be set up before calling set_entries,"
                " because the GUI elements are used as the data source"
                " directly later."
            )
        if version is not None:
            self.version_e.delete(0,tk.END)
            self.version_e.insert(0, version)
        if platform is not None:
            self.pflag_e.delete(0,tk.END)
            self.pflag_e.insert(0, platform)
        if arch is not None:
            self.arch_e.delete(0,tk.END)
            self.arch_e.insert(0, arch)

    def refresh(self):
        # self.set_entries()
        must_contain = self.mgr.parser.get_option('must_contain')
        print("")
        print("Downloading the html page...")
        for label in self.msg_labels:
            label.pack_forget()
        for btn in self.dl_buttons:
            btn.pack_forget()
        self.dl_buttons = []
        self.count_label.config(text="scraping Downloads page...")
        self.root.update()
        self.only_v = self.version_e.get().strip()
        if len(self.only_v) == 0:
            self.only_v = None
        only_p = self.pflag_e.get().strip()
        if len(only_p) == 0:
            only_p = None
        self.only_a = self.arch_e.get().strip()
        if len(self.only_a) == 0:
            self.only_a = None
        elif " " in self.only_a:
            self.only_a = self.only_a.split()
        # Update options to whatever the user sees/changed in the GUI:
        self.mgr.set_options({
            'version': self.only_v,
            'platform': only_p,
            'arch': self.only_a,
        })
        self.v_urls = []
        self.p_urls = []
        self.a_urls = []
        self.urls = self.mgr.get_urls()
        echo0('Of the total {} download url(s) matching "{}"'
              ''.format(len(self.urls), must_contain))
        count = 0
        v_msg = ""
        a_msg = ""
        p_msg = ""
        print("all:")
        if self.only_v is not None:
            v_msg = "{} ".format(self.only_v)
        if self.only_a is not None:
            a_msg = "{} ".format(self.only_a)  # can be a list.
        for url in self.urls:
            if (self.only_v is None) or (self.only_v in url):
                self.v_urls.append(url)
                echo1('- (matched version) "{}"'.format(url))
            else:
                echo1('- "{}" is not version "{}"'.format(url, self.only_v))
        # self.count_label.config(text=v_msg+"count: "+str(len(self.v_urls)))
        print("  matched " + str(len(self.v_urls)) + " " + v_msg + "url(s)")

        print("matching version (tag):")
        for url in self.v_urls:
            if (only_p is None) or (only_p in url):
                self.p_urls.append(url)
                echo1('- (matched platform) "{}"'.format(url))
            else:
                echo1('- "{}" is not for "{}" platform'.format(url, self.only_v))

        print("  matched " + str(len(self.p_urls)) + " " + p_msg + "url(s)")

        user_downloads_path = self.mgr.get_downloads_path()
        self.bn_path = os.path.join(user_downloads_path, "blendernightly")
        self.archives_path = os.path.join(self.bn_path, "archives")

        metas = []
        if isinstance(self.only_a, list):
            arches = self.only_a
        else:
            arches = [self.only_a]
        for url in self.p_urls:
            if (self.only_a is None) or contains_any(url, arches):
                self.a_urls.append(url)
                print(url)
                meta = {}
                meta['url'] = url
                meta['filename'] = name_from_url(url)
                meta['id'] = self.mgr.parser.id_from_url(url, remove_ext=True)
                meta['version'] = self.mgr.parser.blender_tag_from_url(url)
                meta['commit'] = self.mgr.parser.blender_commit_from_url(url)
                metas.append(meta)
                try_dl_path = os.path.join(self.mgr.get_downloads_path(),
                                           meta['filename'])
                dst_dl_path = os.path.join(self.archives_path,
                                           meta['filename'])
                if (os.path.isfile(try_dl_path) and
                        not os.path.isfile(dst_dl_path)):
                    shutil.move(try_dl_path, dst_dl_path)
                    msg = ("collected old download '" + meta['filename'] +
                           "' from Downloads to '" + self.archives_path + "'")
                    print(msg)
                    self.push_label("collected old download:")
                    self.push_label(meta['id'])

        if not os.path.isdir(self.archives_path):
            print("  creating: " + self.archives_path)
            os.makedirs(self.archives_path)
        self.versions_path = os.path.join(self.bn_path, "versions")

        # get already-downloaded versions and see if they are installed
        # (in case certain downloaded builds are no longer available)
        dl_metas = []
        inst_metas = []
        dl_but_not_inst_count = 0
        print("  existing_downloads: ")  # /2.??-<commit>
        added_ids = []
        for dl_name in hierosoft.get_file_names(self.archives_path):
            archive_path = os.path.join(self.archives_path, dl_name)
            dest_id = self.mgr.parser.id_from_url(dl_name, remove_ext=True)
            meta = {}
            dl_metas.append(meta)
            added_ids.append(dest_id)
            self.installed_path = os.path.join(self.versions_path, dest_id)
            meta['downloaded'] = True
            # meta['url'] = None
            meta['filename'] = dl_name
            meta['id'] = dest_id
            meta['version'] = self.mgr.parser.blender_tag_from_url(dl_name)
            meta['commit'] = self.mgr.parser.blender_commit_from_url(dl_name)
            print("  - (archive) '" + self.installed_path + "'")
            bin_path = hierosoft.get_installed_bin(
                self.versions_path,
                meta['id'],
                self.bin_names,
            )
            if bin_path is not None:
                meta['installed_bin'] = bin_path
            else:
                dl_but_not_inst_count += 1
        if self.versions_path is None:
            raise RuntimeError("versions_path is None.")

        for installed_name in hierosoft.get_subdir_names(self.versions_path):
            self.installed_path = os.path.join(self.versions_path, installed_name)
            dest_id = installed_name
            if dest_id in added_ids:
                continue
            meta = {}
            inst_metas.append(meta)
            # ^ formerly self.mgr.parser.id_from_name(installed_name)
            meta['downloaded'] = True
            meta['install_path'] = self.installed_path
            meta['id'] = dest_id
            name_parts = dest_id.split("-")
            meta['version'] = name_parts[0]
            meta['installed'] = True
            if len(name_parts) > 1:
                meta['commit'] = name_parts[1]
            else:
                print("INFO: There is no commit hash in the directory name"
                      " \"{}\"".format(dest_id))
            print("  - (installed) '" + self.installed_path + "'")
            bin_path = hierosoft.get_installed_bin(
                self.versions_path,
                meta['id'],
                self.bin_names,
            )
            if bin_path is not None:
                meta['installed_bin'] = bin_path

        status_s = v_msg + "count: " + str(len(self.a_urls))
        self.count_label.config(text=status_s)
        self.root.update()
        print("  matched " + str(len(self.a_urls)) + " " + a_msg + "url(s)")

        row = 1
        url_installed_count = 0
        for meta in metas + inst_metas:
            # see https://stackoverflow.com/questions/17677649/\
            # tkinter-assign-button-command-in-loop-with-lambda
            user_button = tk.Button(
                self.root,
                text = "Install " + meta['id'],
                command=lambda meta=meta: self.d_click(meta)
            )

            meta['button'] = user_button

            uninstall_caption = "Uninstall"
            if meta.get('installed') is True:
                uninstall_caption = "Remove old"
            else:
                self.dl_buttons.append(user_button)
                user_button.pack()  # grid(row = row, column = 0)
            uninstall_button = tk.Button(
                self.root,
                text = uninstall_caption + " " + meta['id'],
                command=lambda meta=meta: self.uninstall_click(meta)
            )
            meta['uninstall_button'] = uninstall_button
            bin_path = hierosoft.get_installed_bin(
                self.versions_path,
                meta['id'],
                self.bin_names,
            )
            if bin_path is not None:
                meta['installed_bin'] = bin_path
                user_button.config(state=tk.DISABLED)
                if os.path.isfile(bin_path):
                    self.dl_buttons.append(uninstall_button)
                    uninstall_button.pack()  # grid(row = row, column = 0)
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
        if dl_but_not_inst_count > 0:
            self.push_label("Downloaded but not installed ({}):"
                            "".format(dl_but_not_inst_count))
        for meta in dl_metas:
            # see https://stackoverflow.com/questions/17677649/\
            # tkinter-assign-button-command-in-loop-with-lambda
            if meta.get('installed_bin') is None:
                if meta['id'] in ( meta['id'] for meta in metas ):
                    # already is a button
                    continue
                # print("  # not installed: " + meta['filename'])
                user_button = tk.Button(
                    self.root,
                    text = "Install " + meta['id'],
                    command=lambda meta=meta: self.d_click(meta)
                )
                meta['button'] = user_button
                self.dl_buttons.append(user_button)
                user_button.pack()  # grid(row = row, column = 0)

                if meta['id'] in ( meta['id'] for meta in metas ):
                    # already is a button
                    continue
                # print("  # not installed: " + meta['filename'])
                remove_button = tk.Button(
                    self.root,
                    text = "Delete " + meta['id'],
                    command=lambda meta=meta: self.remove_ar_click(meta)
                )
                meta['button'] = remove_button
                self.dl_buttons.append(remove_button)
                remove_button.pack()  # grid(row = row, column = 0)


                row += 1
            # else:
                # print("  # installed: " + meta['filename'])

        self.thread1 = None
        # self.refresh_btn.pack(fill="x")
        # self.refresh_btn.config(fg='black')
        self.refresh_btn.config(state=tk.NORMAL)
        expand = 0
        old_bottom = self.count_label.winfo_y() + self.count_label.winfo_height()
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
        # self.refresh_btn.pack_forget()
        # self.refresh_btn.config(fg='gray')
        # self.refresh()
        if self.thread1 is None:
            echo0("")
            echo0("Starting refresh thread...")
            self.thread1 = threading.Thread(target=self.refresh, args=())
            self.refresh_btn.config(state=tk.DISABLED)
            self.root.update()
            self.thread1.start()
        else:
            echo0("WARNING: Refresh is already running.")

    def refresh_click(self):
        self.start_refresh()


def show_update_window(options):
    root = None
    try:
        root = tk.Tk()
    except tk.TclError:
        echo0("FATAL ERROR: Cannot use tkinter from terminal")
        return 1
    option_keys = MainApplication.get_option_keys()
    for key in option_keys:
        if key not in option_keys:
            raise ValueError("{} is not a valid option.".format(key))
    app = MainApplication(root, options)
    app.pack(side="top", fill="both", expand=True)
    root.after(500, app.start_refresh)
    root.mainloop()
    return 0


def main():
    # Avoid "RuntimeError: main thread is not in main loop"
    # such as on self.count_label.config
    # (not having a separate main function may help).
    options = {}
    options['title'] = "Hierosoft Update"

    # option_keys = MainApplication.get_option_keys()
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
