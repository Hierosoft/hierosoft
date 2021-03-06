#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import traceback
import shutil
import threading
import tarfile
import zipfile

python_mr = sys.version_info.major

if python_mr > 2:  # try:
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
from hierosoft.hplatform import (
    make_shortcut,
)
from hierosoft.hweb import (
    LinkManager,
    name_from_url,
)

# formerly part of blendernightly update.pyw:


def view_traceback(min_indent="  "):
    ex_type, ex, tb = sys.exc_info()
    echo0(min_indent+str(ex_type))
    echo0(min_indent+str(ex))
    traceback.print_tb(tb)
    del tb




# TODO: use classes
class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.root.geometry("1000x600")
        self.root.minsize(600, 400)
        title_s = "Hierosoft Update"
        if len(sys.argv) >= 3:
            if sys.argv[1] == "--title":
                title_s = sys.argv[2]
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
        self.version_e = None
        self.refresh_btn = None
        self.pbar = None
        self.del_arc_var = tk.IntVar()
        default_blender_page_meta = {
            'linArch': "x86_64",  # formerly linux64 formerly x86_64
            'winArch': "amd64",  # formerly windows64
            'darwinArch': ["arm64", "x86_64"],
            # ^ formerly macOS formerly x86_64
        }
        self.mgr = LinkManager(default_blender_page_meta)
        # ^ contains self.mgr.profile_path
        self.dl_buttons = []
        self.msg_labels = []
        self.bin_names = ["blender", "blender.exe"]

        # Formerly before main:
        self.version_e = tk.Entry(self.root)
        self.version_e.delete(0,tk.END)
        self.version_e.insert(0, self.mgr.parser.release_version)
        self.version_e.pack()

        self.pflag_e = tk.Entry(self.root)
        self.pflag_e.delete(0,tk.END)
        self.pflag_e.insert(0, self.mgr.parser.platform_flag)
        self.pflag_e.pack()

        self.arch_e = tk.Entry(self.root)
        self.arch_e.delete(0,tk.END)
        self.arch_e.insert(0, self.mgr.parser.release_arch)
        self.arch_e.pack()

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

    def push_label(self, s):
        new_label = tk.Label(self.root, text=s)
        new_label.pack()
        self.msg_labels.append(new_label)
        self.root.update()

    def d_progress(self, evt):
        if evt['loaded'] - self.shown_progress > 1000000:
            self.shown_progress = evt['loaded']
            self.pbar['value'] = evt['loaded']
            # print(evt['loaded'])
            # evt['total'] is not implemented
            self.count_label.config(text="downloading..." +
                                    str(int(evt['loaded']/1024/1024)) + "MB..")
        self.root.update()

    def d_done(self, evt):
        err = evt.get('error')
        if err is None:
            print("Download finished!")
        else:
            print("Download stopped due to: {}".format(err))
        self.pbar['value'] = 0
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
        update_past_verb = "Updated"
        update_present_verb = "Updating"
        action_present_verb = "Installing"
        action = "install"
        enable_install = True
        if uninstall:
            enable_install = False
            update_past_verb = "Removed"
            update_present_verb = "Removing"
            action_present_verb = "Uninstalling"
            action = "uninstall"
        if remove_download:
            enable_install = False
        for btn in self.dl_buttons:
            btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        btn = meta.get('button')
        uninstall_btn = meta.get("uninstall_button")
        if not uninstall:
            if btn is not None:
                btn.pack_forget()
        else:
            if remove_download:
                if btn is not None:
                    btn.pack_forget()
            if uninstall_btn is not None:
                uninstall_btn.pack_forget()

        self.root.update()
        self.shown_progress = 0
        print("")
        for label in self.msg_labels:
            label.pack_forget()
        print(action_present_verb + ":")
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
        bn_path = os.path.join(user_downloads_path, "blendernightly")
        archives_path = os.path.join(bn_path, "archives")
        if not os.path.isdir(archives_path):
            print("  creating: " + archives_path)
            os.makedirs(archives_path)
        versions_path = os.path.join(bn_path, "versions")
        installed_path = os.path.join(versions_path, dest_id)
        print("  {}: {}".format(action, installed_path))  # /2.??-<commit>
        archive_path = None
        if dl_name is not None:
            archive_path = os.path.join(archives_path, dl_name)
        if enable_install:
            for flag_name in self.bin_names:
                flag_path = os.path.join(installed_path, flag_name)
                if os.path.isfile(flag_path):
                    msg = "Already installed " + meta['id'] + "."
                    print("  already_installed: true")
                    self.count_label.config(text=msg)
                    for btn in self.dl_buttons:
                        btn.config(state=tk.NORMAL)
                    self.refresh_btn.config(state=tk.NORMAL)
                    self.root.update()
                    return

            if not os.path.isfile(archive_path):
                # abs_url should never be None if file already exists
                print("  - downloading: " + abs_url)
                self.mgr.download(archive_path, abs_url,
                                  cb_progress=self.d_progress,
                                  cb_done=self.d_done)
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
        if enable_install:
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
        if remove_download:
            msg = "  - deleting downloaded '" + archive_path + "'..."
            print(msg)
            os.remove(archive_path)
        else:
            if archive_path is not None:
                msg = "  - leaving downloaded '" + archive_path + "'..."
                print(msg)

        if tar is None:
            if enable_install:
                for btn in self.dl_buttons:
                    btn.config(state=tk.NORMAL)
                self.refresh_btn.config(state=tk.NORMAL)
                return
        else:
            print("  fmt: " + fmt)
        tmp_path = os.path.join(bn_path, "tmp")
        if enable_install:
            if not os.path.isdir(tmp_path):
                print("* created {}".format(tmp_path))
                os.makedirs(tmp_path)
        else:
            print("* tmp_path: {}".format(tmp_path))
        # for i in tar:
            # tar.extractfile(i)
        ok = False
        try:
            # if uninstall:
            #     msg = "examining archive..."
            if enable_install:
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
        if enable_install:
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

        if enable_install:
            msg = "moving from tmp..."
            # if uninstall:
            #     msg = "examining extracted tmp..."
            self.count_label.config(text=msg)
            self.root.update()
            # self.push_label(msg)
            print(msg)

        remove_tmp = False
        if not ok:
            remove_tmp = True
        if os.path.isdir(installed_path):
            # msg = "Already installed " + meta['id'] + "."
            meta['installed_bin'] = hierosoft.get_installed_bin(
                versions_path,
                meta['id'],
                self.bin_names,
            )
            if enable_install:
                if make_shortcut(meta, "blender", self.mgr, push_label=self.push_label,
                                 uninstall=uninstall):
                    msg = ("  - {} the old desktop shortcut"
                           "".format(update_past_verb))
                else:
                    msg = ("  - {} the old desktop shortcut failed."
                           "".format(update_present_verb))
                self.count_label.config(text=msg)
                self.root.update()
                remove_tmp = True
            else:
                make_shortcut(meta, "blender", self.mgr, push_label=self.push_label,
                              uninstall=uninstall)
        if remove_tmp:
            if os.path.isdir(tmp_path):
                print("  - deleting temporary '" + tmp_path + "'...")
                shutil.rmtree(tmp_path)
        if ok:
            try:
                if enable_install:
                    print("  - moving {} to {}".format(ext_path,
                                                       installed_path))
                    shutil.move(ext_path, installed_path)
                else:
                    if os.path.isdir(ext_path):
                        print("* WARNING: removing {}".format(ext_path))
                        shutil.rmtree(ext_path)
                    if os.path.isdir(installed_path):
                        print("* uninstalling {}".format(ext_path))
                        shutil.rmtree(installed_path)
                self.count_label.config(text=action+" is complete.")
                print("* {} is complete".format(action))
                if enable_install:
                    if btn is not None:
                        btn.pack_forget()
                else:
                    if uninstall_btn is not None:
                        uninstall_btn.pack_forget()

                self.root.update()
                meta['installed_bin'] = hierosoft.get_installed_bin(
                    versions_path,
                    meta['id'],
                    self.bin_names,
                )
                if enable_install:
                    if make_shortcut(meta, "blender", self.mgr,
                                     push_label=self.push_label,
                                     uninstall=uninstall):
                        msg = ("{} the desktop shortcut"
                               "".format(update_past_verb))
                    else:
                        msg = ("{} the desktop shortcut failed."
                               "".format(update_present_verb))
                else:
                    make_shortcut(meta, "blender", self.mgr,
                                  push_label=self.push_label,
                                  uninstall=uninstall)
            except:
                msg = action + " could not finish moving"
                if uninstall:
                    msg = action + " could not finish deleting"
                self.push_label(msg)
                self.count_label.config(text="Installation failed.")
                self.root.update()
                self.push_label("to " + meta['id'])
                print("  from (extracted) '" + ext_path + "'")
                print(msg)
                print("  to '" + installed_path + "'")
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

    def refresh(self):
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
        self.mgr.parser.release_version = self.only_v
        self.mgr.parser.platform_flag = only_p
        self.mgr.parser.release_arch = self.only_a
        self.v_urls = []
        self.p_urls = []
        self.a_urls = []
        self.urls = self.mgr.get_urls(verbose=False,
                                      must_contain="/blender-")
        print("Of the total " + str(len(self.urls)) + " blender download url(s)")
        count = 0
        v_msg = ""
        a_msg = ""
        p_msg = ""
        print("all:")
        if self.only_v is not None:
            v_msg = self.only_v + " "
        if self.only_a is not None:
            a_msg = self.only_a + " "
        for url in self.urls:
            if (self.only_v is None) or (self.only_v in url):
                self.v_urls.append(url)
                print(url)
        # self.count_label.config(text=v_msg+"count: "+str(len(self.v_urls)))
        print("  matched " + str(len(self.v_urls)) + " " + v_msg + "url(s)")

        print("matching version (tag):")
        for url in self.v_urls:
            if (only_p is None) or (only_p in url):
                self.p_urls.append(url)
                print(url)

        print("  matched " + str(len(self.p_urls)) + " " + p_msg + "url(s)")

        user_downloads_path = self.mgr.get_downloads_path()
        bn_path = os.path.join(user_downloads_path, "blendernightly")
        archives_path = os.path.join(bn_path, "archives")

        metas = []
        for url in self.p_urls:
            if (self.only_a is None) or (self.only_a in url):
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
                dst_dl_path = os.path.join(archives_path,
                                           meta['filename'])
                if (os.path.isfile(try_dl_path) and
                        not os.path.isfile(dst_dl_path)):
                    shutil.move(try_dl_path, dst_dl_path)
                    msg = ("collected old download '" + meta['filename'] +
                           "' from Downloads to '" + archives_path + "'")
                    print(msg)
                    self.push_label("collected old download:")
                    self.push_label(meta['id'])

        if not os.path.isdir(archives_path):
            print("  creating: " + archives_path)
            os.makedirs(archives_path)
        versions_path = os.path.join(bn_path, "versions")

        # get already-downloaded versions and see if they are installed
        # (in case certain downloaded builds are no longer available)
        dl_metas = []
        inst_metas = []
        dl_but_not_inst_count = 0
        print("  existing_downloads: ")  # /2.??-<commit>
        added_ids = []
        for dl_name in hierosoft.get_file_names(archives_path):
            archive_path = os.path.join(archives_path, dl_name)
            dest_id = self.mgr.parser.id_from_url(dl_name, remove_ext=True)
            meta = {}
            dl_metas.append(meta)
            added_ids.append(dest_id)
            installed_path = os.path.join(versions_path, dest_id)
            meta['downloaded'] = True
            # meta['url'] = None
            meta['filename'] = dl_name
            meta['id'] = dest_id
            meta['version'] = self.mgr.parser.blender_tag_from_url(dl_name)
            meta['commit'] = self.mgr.parser.blender_commit_from_url(dl_name)
            print("  - (archive) '" + installed_path + "'")
            bin_path = hierosoft.get_installed_bin(
                versions_path,
                meta['id'],
                self.bin_names,
            )
            if bin_path is not None:
                meta['installed_bin'] = bin_path
            else:
                dl_but_not_inst_count += 1
        if versions_path is None:
            raise RuntimeError("versions_path is None.")

        for installed_name in hierosoft.get_subdir_names(versions_path):
            installed_path = os.path.join(versions_path, installed_name)
            dest_id = installed_name
            if dest_id in added_ids:
                continue
            meta = {}
            inst_metas.append(meta)
            # ^ formerly self.mgr.parser.id_from_name(installed_name)
            meta['downloaded'] = True
            meta['install_path'] = installed_path
            meta['id'] = dest_id
            name_parts = dest_id.split("-")
            meta['version'] = name_parts[0]
            meta['installed'] = True
            if len(name_parts) > 1:
                meta['commit'] = name_parts[1]
            else:
                print("INFO: There is no commit hash in the directory name"
                      " \"{}\"".format(dest_id))
            print("  - (installed) '" + installed_path + "'")
            bin_path = hierosoft.get_installed_bin(
                versions_path,
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
                versions_path,
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
                  "".format(versions_path))
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
            print("")
            print("Starting refresh thread...")
            self.thread1 = threading.Thread(target=self.refresh, args=())
            self.refresh_btn.config(state=tk.DISABLED)
            self.root.update()
            self.thread1.start()
        else:
            print("WARNING: Refresh is already running.")

    def refresh_click(self):
        self.start_refresh()

def main():
    # Avoid "RuntimeError: main thread is not in main loop"
    # such as on self.count_label.config
    # (not having a separate main function may help).
    root = None
    try:
        root = tk.Tk()
    except tk.TclError:
        echo0("FATAL ERROR: Cannot use tkinter from terminal")
        sys.exit(1)

    app = MainApplication(root)
    app.pack(side="top", fill="both", expand=True)
    root.after(500, app.start_refresh)
    root.mainloop()

if __name__ == "__main__":
    main()
