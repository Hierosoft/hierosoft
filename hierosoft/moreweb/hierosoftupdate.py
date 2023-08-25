import copy
import os
import platform
import shutil
import sys
import time
import zipfile

from pprint import pformat

MOREWEB_SUBMODULE_DIR = os.path.dirname(os.path.realpath(__file__))
MODULE_DIR = os.path.dirname(MOREWEB_SUBMODULE_DIR)
REPO_DIR = os.path.dirname(MODULE_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

from hierosoft import (
    echo0,
    echo1,
    echo2,
    get_file_names,
    get_installed_bin,
    get_subdir_names,
    get_missing_paths,
    HOME,
    USER_PROGRAMS,
    CACHES,
    ASSETS_DIR,
    which_python,
    join_if_exists,
)
from hierosoft.ggrep import (
    contains_any,
)

from hierosoft.moreplatform import (
    install_zip,
    make_shortcut,
    install_archive,
)

from hierosoft.moreweb import (
    name_from_url,
    STATUS_DONE,
    get_python_download_spec,
)

from hierosoft.moreweb.downloadmanager import DownloadManager


def i_am_static_build():
    prefix = "[i_am_static_build] "
    nearby_init = os.path.join(MOREWEB_SUBMODULE_DIR, "__init__.py")
    if not os.path.isfile(nearby_init):
        echo0(prefix+"Not static: no %s" % pformat(nearby_init))
        return False
    # If it exists, it still may be just a random file on the desktop,
    #   so check if I am myself *and* in the real directory:
    self_py = os.path.realpath(__file__)
    expected_self_py = os.path.join(
        MOREWEB_SUBMODULE_DIR,
        "hierosoftupdate.py",
    )
    if self_py != expected_self_py:
        echo0(prefix+"Not static: Executing script %s is not %s"
              % (pformat(self_py), pformat(expected_self_py)))
        return False
    mydir_name = os.path.basename(MOREWEB_SUBMODULE_DIR)
    expected_mydir_name = "moreweb"
    if mydir_name != expected_mydir_name:
        echo0(prefix+"Not static: %s's directory %s is not %s"
              % (pformat(__file__),
                 pformat(mydir_name),
                 pformat(expected_mydir_name)))
        return False
    module_dir_name = os.path.basename(MODULE_DIR)
    expected_module_dir_name = "hierosoft"
    if module_dir_name != expected_module_dir_name:
        echo0(prefix+"Not static: %s's parent directory %s is not %s"
              % (pformat(mydir_name),
                 pformat(module_dir_name),
                 pformat(expected_module_dir_name)))
        return False
    echo0(prefix+"Yes")
    return True


class HierosoftUpdate(object):
    """Install the rest of hierosoft.
    Args:
        parent: (ignored) reserved for sub-classes or alike-classes.
        root: (ignored) reserved for sub-classes or alike-classes.
        options (dict): a download spec
    """
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

    def __init__(self, parent, root, options):
        # For docstring see class.
        self.root = None
        # region for d_done
        # TODO: Move all/most of these to a new DownloadJob class?
        self.auto_column = 0
        self.auto_row = 0
        self.download_done = False
        self.archive_path = None
        self.enable_install = None
        self.remove_download = None
        self.luid = None
        self.programs = USER_PROGRAMS
        self.installed_path = None
        self.action = None
        self.uninstall = None  # TODO: move this to the event
        self.meta = None
        self.update_past_verb = None
        self.update_present_verb = None
        self.action_present_verb = None
        # endregion for d_done

        self.options = {}  # gathers *relevant* values from options
        #  (See get_option_keys & set_options call below).

        self.best_python = which_python()
        # ^ Even if not i_am_static_build(), a Python is useful
        #   for running downloaded applications.
        self.urls = None
        self.count_label = None
        self.refresh_btn = None
        self.dl_buttons = []
        self.msg_labels = []
        self.events = []
        self.pbar = None
        self.statusVar = None  # for subclass: set to StringVar or similar

        self.v_urls = None  # urls matching specified Blender version (tag)
        self.p_urls = None  # urls matching specified platform flag
        self.a_urls = None  # urls matching specified architecture
        self.option_entries = {}
        self.mgr = DownloadManager()
        self.set_all_options(options, True, require_bin=False)
        # ^ sets *relevant* keys on self, mgr, parser
        title = self.options.get('title')
        if title is not None:
            echo0("Initializing %s" % title)

    def set_luid(self, luid):
        if luid is None:
            raise ValueError("LUID (program dirname) is None.")
        if " " in luid:
            raise ValueError("LUID (program dirname) cannot contain spaces.")
        self.luid = luid

    @property
    def luid_dir(self):
        return os.path.join(self.programs, self.luid)

    @property
    def archives_path(self):
        return os.path.join(CACHES, self.luid, "archives")  # zips

    @property
    def versions_path(self):
        return os.path.join(self.luid_dir, "versions")

    def get_this_version_path(self, version):
        return os.path.join(self.versions_path, version)

    def set_status(self, msg):
        if self.statusVar is not None:
            self.statusVar.set(msg)
        else:
            echo0("%s" % msg)

    @property
    def only_a(self):
        return self.options.get('arch')

    @property
    def bin_names(self):
        return self.options.get('bin_names')

    @property
    def only_p(self):
        return self.options.get('platform')

    @property
    def only_v(self):
        return self.options.get('version')

    @staticmethod
    def get_option_keys():
        """Get which options are used by this class.
        Should be same for all subclasses
        """
        return (
            ['version', 'platform', 'arch', 'bin_names', 'exists_action']
            + list(HierosoftUpdate.HELP.keys())
            # + DownloadManager.get_option_keys())
            # FIXME: ^ Why was this here?
        )

    def set_all_options(self, options, set_gui_fields, require_bin=True):
        """Set options for the next refresh.

        Args:
            set_gui_fields (bool): Set to false if called by
                fields_to_settings to avoid infinite recursion.
            options (dict): Options that apply to mgr
                (which will apply parser options to parser).
        """
        # FIXME: See if use of set_gui_fields is really right & necessary here
        prefix = "[set_options] "
        self.download_done = False
        echo0(prefix+"running")
        for key, value in options.items():
            if key in DownloadManager.get_option_keys():
                self.mgr.set_mgr_and_parser_options({key: value})
            elif key == "platforms":
                self.mgr.set_mgr_and_parser_options({
                    'platform': value[platform.system()],
                })
            elif key == "architectures":
                self.mgr.set_mgr_and_parser_options({
                    'arch': value[platform.system()],
                })
            elif key in HierosoftUpdate.get_option_keys():
                self.options[key] = value
            else:
                raise KeyError("Invalid option: %s=%s" % (key, value))
        if require_bin:
            if self.bin_names is None:
                raise ValueError(
                    "You must set bin_names before refresh (got None)."
                )
        # ^ bin_names is required but may not be available when __init__ calls
        # ^ These attributes may change based on GUI fields in a GUI subclass
        if set_gui_fields:
            self.settings_to_fields()

    def settings_to_fields(self):
        """A GUI subclass must override & prefill fields with initial values

        Subclass should set only_v, only_p, and only_a from the GUI fields.
        """
        pass

    def fields_to_settings(self):
        """Override this in the GUI subclass to process & validate form.
        """
        pass

    def _download_page(self):
        prefix = "_download_page"
        if self.mgr.parser is None:
            raise RuntimeError("The parser was not initialized"
                               " (run self.mgr.set_options first).")
        self.must_contain = self.mgr.parser.get_option('must_contain')
        echo0("")
        echo0(prefix+"Downloading the html page...")
        self.dl_buttons = []
        self.mgr.set_mgr_and_parser_options({
            'version': self.only_v,
            'platform': self.only_p,
            'arch': self.only_a,
        })
        self.v_urls = []
        self.p_urls = []
        self.a_urls = []
        self.urls = self.mgr.get_urls()
        echo0('Of the total {} download url(s) matching "{}"'
              ''.format(len(self.urls), self.must_contain))
        # count = 0
        self.v_msg = ""
        self.a_msg = ""
        self.p_msg = ""
        print("all:")
        if self.only_v is not None:
            self.v_msg = "{} ".format(self.only_v)
        if self.only_a is not None:
            self.a_msg = "{} ".format(self.only_a)  # can be a list.
        for url in self.urls:
            if (self.only_v is None) or (self.only_v in url):
                self.v_urls.append(url)
                echo1('- (matched version) "{}"'.format(url))
            else:
                echo1('- "{}" is not version "{}"'.format(url, self.only_v))
        # self.count_label.config(text=self.v_msg+"count:%s"%len(self.v_urls))
        print("  matched {} {}url(s)".format(len(self.v_urls), self.v_msg))

        print("matching version (tag):")
        for url in self.v_urls:
            if (self.only_p is None) or (self.only_p in url):
                self.p_urls.append(url)
                echo1('- (matched platform) "{}"'.format(url))
            else:
                echo1('- "%s" is not for "%s" platform' % (url, self.only_v))

        print("  matched {} {}url(s)".format(len(self.p_urls), self.p_msg))

        if self.luid is None:
            raise ValueError(
                'Run set_luid first on HierosoftUpdate instance'
                ' (program-specific directory for "versions" and "archives")'
            )

        self.link_metas = []
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
                meta['detected_luid'] = self.mgr.parser.id_from_url(
                    url,
                    remove_ext=True,
                )
                if self.luid is not None:
                    meta['luid'] = self.luid
                meta['version'] = self.mgr.parser.blender_tag_from_url(url)
                meta['commit'] = self.mgr.parser.blender_commit_from_url(url)
                self.link_metas.append(meta)
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
                    self.push_label(meta['detected_luid'])
        if self.archives_path is None:
            raise RuntimeError(
                "Run set_luid on HierosoftUpdate instance first"
            )
        if not os.path.isdir(self.archives_path):
            print("  creating: " + self.archives_path)
            os.makedirs(self.archives_path)

        # get already-downloaded versions and see if they are installed
        # (in case certain downloaded builds are no longer available)
        self.dl_metas = []
        self.installed_metas = []
        self.dl_but_not_inst_count = 0
        print("  existing_downloads: ")  # /2.??-<commit>
        added_ids = []
        for dl_name in get_file_names(self.archives_path):
            # archive_path = os.path.join(self.archives_path, dl_name)
            dest_id = self.mgr.parser.id_from_url(dl_name, remove_ext=True)
            meta = {}
            self.dl_metas.append(meta)
            added_ids.append(dest_id)
            self.installed_path = os.path.join(self.versions_path, dest_id)
            meta['downloaded'] = True
            # meta['url'] = None
            meta['filename'] = dl_name
            meta['detected_luid'] = dest_id
            luid = dest_id
            if self.luid is not None:
                meta['luid'] = self.luid
                luid = self.luid
            meta['version'] = self.mgr.parser.blender_tag_from_url(dl_name)
            meta['commit'] = self.mgr.parser.blender_commit_from_url(dl_name)
            print("  - (archive) '" + self.installed_path + "'")
            bin_path = get_installed_bin(
                self.versions_path,
                luid,
                self.bin_names,
            )
            if bin_path is not None:
                meta['Exec'] = bin_path
            else:
                self.dl_but_not_inst_count += 1
        if self.versions_path is None:
            raise RuntimeError("versions_path is None.")

        for installed_name in get_subdir_names(self.versions_path):
            self.installed_path = os.path.join(self.versions_path,
                                               installed_name)
            dest_id = installed_name
            if dest_id in added_ids:
                continue
            meta = {}
            self.installed_metas.append(meta)
            # ^ formerly self.mgr.parser.id_from_name(installed_name)
            meta['downloaded'] = True
            meta['install_path'] = self.installed_path
            meta['luid'] = dest_id
            name_parts = dest_id.split("-")
            meta['version'] = name_parts[0]
            meta['installed'] = True
            if len(name_parts) > 1:
                meta['commit'] = name_parts[1]
            else:
                print("INFO: There is no commit hash in the directory name"
                      " \"{}\"".format(dest_id))
            print("  - (installed) '" + self.installed_path + "'")
            bin_path = get_installed_bin(
                self.versions_path,
                meta['luid'],
                self.bin_names,
            )
            if bin_path is not None:
                meta['Exec'] = bin_path

    def d_progress(self, evt):
        '''Handle done events such as for downloads.
        This just appends an even so it doesn't have to run on the main thread
        (Therefore, don't access the GUI directly here).

        For the actual event logic, see _d_progress which is run by
        _process_events on the main thread.
        '''
        pass
        event = copy.deepcopy(evt)
        event['command'] = "d_progress"
        ratio = event.get('ratio')
        if 'loaded' in evt:
            sys.stderr.write(
                "\r{} of {}".format(evt['loaded'], evt['total_size'])
            )
        elif ratio is not None:
            sys.stderr.write("\r{}%".format(round(ratio*100, 1)))
        sys.stderr.flush()
        # GUI overload should skip output above:
        self.events.append(event)

    def d_click(self, meta, uninstall=False, remove_download=False,
                cb_done=None):
        """Download the version (or skip if downloaded) & install.

        When the download is complete (or was already downloaded),
        the actual install is done by whatever is called by
        _process_event (event is enqueued by d_done) unless custom
        cb_done is set, then your cb_done must accept evt (event
        dictionary) and take action on the file (evt[''])

        Args:
            meta (dict): metadata about the software. Since this
                is specific to this program, a lambda or similar
                structure is necessary to call d_click if a GUI
                button is clicked (since for example, a tk click
                event is *not* valid).
            cb_done (dict): Force a synchronous event instead of
                using d_done and _process_events. This is useful
                for CLI applications where the user can't click
                to install a Python program such as Hierosoft if
                this run is installing Python.
        """
        evt = copy.deepcopy(meta)
        self.meta = meta
        self.remove_download = remove_download
        self.uninstall = uninstall
        self.update_past_verb = "Updated"
        self.update_present_verb = "Updating"
        self.action_present_verb = "Installing"
        self.action = "install"
        self.enable_install = True
        done_is_synchronous = False
        if cb_done is None:
            cb_done = self.d_done
        else:
            done_is_synchronous = True
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
        if self.refresh_btn is not None:
            self.refresh_btn.config(state=tk.DISABLED)
        self.download_clicked_btn = meta.get('button')
        uninstall_btn = meta.get("uninstall_button")
        if not uninstall:
            if self.download_clicked_btn is not None:
                self.download_clicked_btn.grid_remove()
        else:
            if remove_download:
                if self.download_clicked_btn is not None:
                    self.download_clicked_btn.grid_remove()
            if uninstall_btn is not None:
                uninstall_btn.grid_remove()
        if self.root is not None:
            self.root.update()
        self.shown_progress = 0
        print("")
        for label in self.msg_labels:
            label.grid_remove()
        print(self.action_present_verb + ":")
        print("  version: " + meta['version'])
        print("  commit: " + meta['commit'])
        if self.pbar is not None:
            self.pbar['maximum'] = 200*1024*1024  # TODO: get actual MB count
            self.pbar['value'] = 0
        url = meta.get('url')
        abs_url = None
        if url is not None:
            abs_url = self.mgr.absolute_url(url)

        dest_id = meta.get('luid')
        if dest_id is None:
            dest_id = self.mgr.parser.id_from_name(meta['filename'],
                                                   remove_ext=True)
        # print("new_filename: " + self.mgr.parser.id_from_url(url))
        dl_name = meta.get('filename')  # name_from_url(url)
        if self.archives_path is None:
            raise RuntimeError(
                "Run set_luid on HierosoftUpdate instance first."
            )
        if not os.path.isdir(self.archives_path):
            print("  creating: " + self.archives_path)
            os.makedirs(self.archives_path)
        self.installed_path = os.path.join(self.versions_path, dest_id)
        print("action={}: {}".format(self.action, self.installed_path))
        # /2.??-<commit>
        self.archive_path = None
        if dl_name is not None:
            self.archive_path = os.path.join(self.archives_path, dl_name)
        # if not self.enable_install:
        #     echo0("enable_install={}".format(self.enable_install))
        #     return evt

        total_count = 0
        missing_paths = get_missing_paths(self.installed_path, self.bin_names)
        evt['already_installed'] = False
        if not missing_paths:
            msg = "Already installed " + meta['luid'] + "."
            print("  already_installed: true")
            self.push_label(msg)
            # All of this GUI stuff will be None if not using GUI subclass
            if self.count_label:
                self.count_label.config(text=msg)
            for btn in self.dl_buttons:
                btn.config(state=tk.NORMAL)
            if self.refresh_btn:
                self.refresh_btn.config(state=tk.NORMAL)
            if self.root:
                self.root.update()
            if evt.get('exists_action') != "delete":
                evt['already_installed'] = True
                evt['installed_path'] = self.installed_path
                evt['bin_names'] = self.bin_names
                evt['status'] = STATUS_DONE
                return evt
        print("* done checking for {} binaries".format(total_count))

        # TODO: self_install_options['exists_action'] may be "delete" or "skip"

        evt = copy.deepcopy(meta)
        # evt.update(event_template)
        evt['archive'] = self.archive_path
        # ^ triggers extract
        evt['luid'] = self.luid
        if os.path.isfile(self.archive_path):
            self.push_label("Warning: Resuming install with existing archive")
            self.push_label(self.archive_path)
            echo0('* archive_path="{}": archive is already downloaded'
                  ''.format(self.archive_path))  # self.action
            evt['status'] = STATUS_DONE
            cb_done(evt)  # usually a thread could call this
            if not done_is_synchronous:
                self._process_events()
            else:
                if not evt.get('installed_path'):
                    raise NotImplementedError("installed_path must be set")
            return evt

        # abs_url should never be None if file already exists
        print("  - downloading: " + abs_url)
        with open(self.archive_path, 'wb') as f:
            self.download_done = False
            self.mgr.download(
                f,
                abs_url,
                cb_progress=self.d_progress,
                cb_done=cb_done,
                evt=evt,
            )
            while not self.download_done:
                # Keep the file open until the download completes
                #   or fails.
                # TODO: timeout
                time.sleep(.25)
                self._process_events()
        if not evt.get('installed_path'):
            raise NotImplementedError("installed_path must be set")
        return evt

    def d_done(self, evt):
        '''Handle done events such as for downloads.
        This just appends an even so it doesn't have to run on the main thread
        (Therefore, don't access the GUI directly here).

        For the actual event logic, see _process_event on the main thread.
        '''
        self.download_done = True
        event = copy.deepcopy(evt)
        event['command'] = "d_done"
        self.events.append(event)

    def _d_progress(self, evt):
        """This should only be called by _process_events
        on the main thread (other threads will throw access violation
        trying to access the GUI).

        The GUI should override this and show progress to the GUI user.

        For the generic event handler, use self.d_progress
        instead (to append an event to the event queue).
        """
        sys.stderr.write("\rprogress: %s" % evt)
        sys.stderr.flush()

    def _on_archive_ready(self, evt):
        """This should only be called by _process_events
        on the main thread (other threads will throw access violation
        trying to access the GUI).

        For the generic event handler, use self.d_done
        instead (to append an event to the event queue).
        """
        # formerly _d_done
        # prefix = "[_on_archive_ready]"
        echo0("")  # end the line that _d_progress started.
        echo0("done: %s" % evt)
        # region move to event_template
        # meta = self.meta
        # meta = evt
        # archive = self.archive_path
        # endregion moved to event_template
        archive = evt['archive']
        if self.download_done:
            echo0("Warning: download is already done.")
        self.download_done = True
        if self.pbar:
            self.pbar['value'] = 0
        err = evt.get('error')
        # version = meta['version']
        # self.set_luid(evt['luid'])
        version = evt['version']  # such as "main" if getting master zip
        # ^ multi-version structure required (unlike nopackage where optional)
        archive = evt.get('archive')  # caller must set even cached (not dl)
        # luid_dir = self.luid_dir
        # ^ usually same as:
        # luid_dir = os.path.join(self.programs, luid)
        # However, with multi-version, use:
        versions_path = self.versions_path
        # ^ usually same as:
        # versions_path = os.path.join(luid_dir, "versions")
        program_dir = os.path.join(versions_path, version)
        if err is None:
            print("Download finished!")
        else:
            print("Download stopped due to: {}".format(err))
            return
        if self.enable_install and archive is not None:
            self.meta['Path'] = program_dir
            installed = install_archive(
                archive,
                program_dir,
                remove_archive=self.remove_download,
                event_template=evt,
            )
            # ^ Automatically removes tier if root of zip is only one dir
            extracted_name = installed.get('extracted_name')
            if extracted_name:
                evt['extracted_name'] = extracted_name
                echo0("Extracted %s" % extracted_name)
            echo0("Installed %s" % program_dir)
            error = installed.get('error')
            if error:
                self.push_label(error)
                self.set_status("Extracting failed. Try download again.")
            else:
                # if not evt.get('luid') == 'hierosoft':
                #     echo0("Making shortcut since %s (not hierosoft)")
                #     make_shortcut(result)
                # TODO: add "add shortcut" button (and/or checkbox in install)
                self.set_status("Done: %s" % installed)
        elif self.enable_install is not None:
            self.set_status("Error: Install is enabled but archive not set.")
        else:
            self.set_status("Install is not enabled for %s"
                            % (pformat(archive)))

        for btn in self.dl_buttons:
            btn.config(state=tk.NORMAL)
        if self.refresh_btn:
            self.refresh_btn.config(state=tk.NORMAL)
        if self.root:
            self.root.update()
        self.meta = None  # TODO: remove this and use evt throughout

    def _process_event(self, event):
        echo2("* processing {}".format(event))
        command = event.get('command')
        # caller = event.get('caller')
        if command is None:
            echo0("Error: command is one for event={}".format(event))
            # return None
            return
        elif command == "d_progress":
            self._d_progress(event)
            # return event
        elif command == "d_done":
            self._on_archive_ready(event)
            # ^ This is ok for now since it checks what is
            #   being done and checks self.
            """
            if caller == "prepare_and_run_launcher":
                self._on_archive_ready(event)
            elif caller == "install_blender":
                self._on_archive_ready(event)
            else:
                echo0("Done (no default actions nor cb_done configured): %s"
                      % event)
            """
            # return event
        else:
            echo0("Error: command '{}' is unknown for event={}"
                  "".format(command, event))
        # return None

    def _process_events(self):
        '''
        Process each event dictionary in self.events and use the command
        to determine what to do. This occurs on the main thread such as
        in case the main thread is a GUI, which threads may not be
        able to access in some frameworks. Instead, threads should
        append events to self.events, and the main thread should poll
        the outcome of calls by calling this and checking for some state
        such as one that "d_done" (or the _on_archive_ready event)
        sets, otherwise should set its own cb_done. However, the GUI
        implementation of _process_event can set the state and enable
        buttons to allow the user to choose the next action.

        Before adding an event to self.events, making a deepcopy is
        recommended (especially before adding 'command' where
        applicable).
        '''
        while len(self.events) > 0:
            event = self.events[0]
            del self.events[0]
            self._process_event(event)
        # return done_events

    def push_label(self, text):
        sys.stderr.write("[status] %s..." % text)
        sys.stderr.flush()

    def _d_done_downloading_update(self, event):
        prefix = "[_d_done_downloading_update] "
        echo0(prefix+"Update info: %s" % event)

    def download_first(self, event_template=None):
        """

        Args:
            event_template (dict): A copy of this along with any
                event information gathered will be returned
                along with this.
                The following may be set:
                - any keys in meta (first meta in self.link_metas
                  + self.installed_metas).
                - 'error' (string): Is set on error.
                - see also d_click
        """
        done = False
        if event_template:
            if 'error' in event_template:
                raise ValueError(
                    "error is already set in event_template: %s"
                    % event_template['error']
                )
            evt = copy.deepcopy(event_template)
        else:
            evt = {}
        for meta in self.link_metas:  # + self.installed_metas:
            if done:
                echo0('Warning: Skipped extra: %s' % meta)
                continue
            self.set_status("Downloading %s..." % meta.get('name'))
            if self.root is not None:
                self.root.update()
            evt.update(meta)
            downloaded = self.d_click(evt)
            evt.update(downloaded)
            done = True
        if not done:
            evt['error'] = "No matching URL found."
        return evt

    def refresh(self):
        # prefix = "[refresh] "
        self._download_page()
        return self.download_first()
        # ^ merely calls self.d_click(evt) on first meta
        #   in self.link_metas (not self.installed_metas)

    def echo_md(self):
        raise NotImplementedError("echo_md")

    def start_refresh(self):
        """
        This should match start_refresh in HierosoftUpdateFrame
        except run no dependencies.
        """
        self.refresh()  # GUI would start a thread instead
        # Do not schedule--CLI may have to do successive downloads/steps


enable_tk = False

default_sources = {
    'default_sources_urls': [  # URLs for data to update default_sources itself
        ("https://github.com/Hierosoft/hierosoft"
         "/blob/main/hierosoft/assets/data/default_sources.json"),
        "https://minetest.io/launcherapi/sources.json",
    ],
    'self_install_sources': [
        {
            'title': "Hierosoft Launcher",
            'version': "current",  # formerly parser.release_version
            # ^ formerly  "/download//blender-*"
            'must_contain': "/Hierosoft/hierosoft/archive/refs/heads/main.zip",
            'html_url': "https://github.com/Hierosoft/hierosoft",
            'base_url': "https://github.com",  # Prepend this not html_url
            'bin_names': ["run.pyw"],
        },
    ],
}
# ^ Overwrites hierosoft/data/default_sources.json only if
#   ~/metaprojects/hierosoft-developer.flag exists.

data_dir = os.path.join(ASSETS_DIR, "data")
sources_path = os.path.join(data_dir, "default_sources.json")
# for developer only:
if os.path.isfile(os.path.join(HOME, "metaprojects",
                               "hierosoft-developer.flag")):
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(data_dir)
    import json
    with open(sources_path, 'w') as stream:
        json.dump(default_sources, stream, indent=2, sort_keys=True)


def main():
    """Run Hierosoft update without a GUI to install the GUI.

    __init__.py will pick itself up by the bootstraps and install
    the rest of hierosoft!
    """
    prefix = "[hierosoftupdate main] "
    global enable_tk
    root = None
    upgrade = False  # Don't upgrade without --upgrade (but install if missing)
    for argi, arg in enumerate(sys.argv):
        if argi == 0:
            continue
        if arg == "--upgrade":
            upgrade = True
    if enable_tk:
        root = tk.Tk()
        statusVar = tk.StringVar()
        screenW = root.winfo_screenwidth()
        screenH = root.winfo_screenheight()
        winW1 = int(float(screenW)/3.0)
        winH1 = int(float(screenH)/3.0)
        if winH1 < winW1:
            # widescreen
            # Enforce 3:2 ratio:
            winW = int(float(winH1) * 1.5)
            winH = winH1
            if winW > screenW:
                winW = screenW
                winH = int(float(winW) / 1.5)
        else:
            # narrow screen
            # Enforce 2:3 ratio
            winH = int(float(winW1) * 1.5)
            winW = winW1
            if winH > screenH:
                winH = screenH
                winW = int(float(winH) / 1.5)
        root.title("")   # "Tk" by default.
        left = int((screenW - winW) / 2)
        top = int((screenH - winH) / 2)
        root.geometry("%sx%s+%s+%s" % (winW, winH, left, top))
        pointSize = float(screenW) / 14.0 / 72.0  # assume 14" approx screen
        canvas = tk.Canvas(
            width=winW,
            height=winH-int(pointSize*20.0),
        )
        label = tk.Label(
            root,
            textvariable=statusVar,
        )
        statusVar.set("Preparing...")
        canvas.pack(
            side=tk.TOP,
            fill=tk.BOTH,
            expand=True,
        )
        label.pack(
            side=tk.BOTTOM,
            fill=tk.BOTH,
            expand=True,
        )
        from hierosoft.hierosoftpacked import hierosoft_svg
        from hierosoft.moresvg import MoreSVG
        # def after_size():
        root.update()
        # ^ finalizes size (otherwise constrain fails due to
        #   incorrect canvas.winfo_width() or winfo_height())
        test_only = False
        if test_only:
            canvas.create_polygon(10,10,canvas.winfo_width(),60, 0,60, 10, 10,
                                  fill="black", smooth=1)
        svg = MoreSVG()
        pos = [
            int((winW - winH) / 2),  # this centering assumes square graphic
            0,
        ]
        if not test_only:
            svg.draw_svg(
                hierosoft_svg,
                canvas,
                constrain="height",
                pos=pos,
            )

    self_install_options = copy.deepcopy(default_sources['self_install_sources'][0])
    # TODO: ^ Try another source if it fails, or random for load balancing.

    app = HierosoftUpdate(None, None, self_install_options)
    wait_for_python = False
    if platform.system() == "Windows":
        # In case this is an exe, install Python if not present
        if not app.best_python:
            app.statusVar = statusVar
            python_meta = get_python_download_spec()
            app.set_all_options(python_meta, True)
            app.start_refresh()  # synchronous since CLI superclass
            # region prepare_and_run_launcher args
            python_meta['next_app'] = app
            python_meta['next_root'] = root
            python_meta['next_enable_upgrade'] = upgrade
            # endregion prepare_and_run_launcher args
            installed = app.download_first(
                cb_done=prepare_and_run_launcher,
                event_template=python_meta,
            )
            # ^ installed *Python*
            # ^ merely calls self.d_click(evt) on first meta
            #   in self.link_metas + self.installed_metas
            wait_for_python = True
        else:
            echo0(prefix+"Using %s" % app.best_python)
    if not wait_for_python:
        self_install_options['next_app'] = app
        self_install_options['next_root'] = root
        self_install_options['next_enable_upgrade'] = upgrade
        prepare_and_run_launcher(self_install_options)


def prepare_and_run_launcher(self_install_options):
    """Install self

    This should be the cb_done callback for Python install,
    but if Python is already installed this should be called
    right away to install Python version of Hierosoft
    and run it.
    """
    prefix = "[prepare_and_run_launcher] "
    error = self_install_options.get('error')
    if error:
        raise RuntimeError("Installing Python failed: %s" % error)
    app = self_install_options['next_app']
    del self_install_options['next_app']
    root = self_install_options['next_root']
    del self_install_options['next_root']
    upgrade = self_install_options['next_enable_upgrade']
    del self_install_options['next_enable_upgrade']
    self_install_options['exists_action'] = "delete" if upgrade else "skip"
    app.set_all_options(self_install_options, True)
    # TODO: check dl_but_not_inst_count
    # if enable_tk:
    #     app.root = root
    #     root.after(50, app.refresh)
    #     root.mainloop()
    # else:
    app.set_luid("hierosoft")  # other programs should say their own dir name
    if root is not None:
        root.update()
    app.set_status("Loading...")
    app.enable_install = True
    # app.start_refresh()  # synchronous since CLI superclass
    # but use explicitly synchronous version:
    # app.refresh()
    # but to get return as well:
    # version = self_install_options['version']
    # FIXME: should be "current" for main branch but isn't getting passed down
    version = "main"
    good_installed_path = app.get_this_version_path(version)
    try_launch_scripts = ["run.pyw", "run.py", "main.py"]
    start_script = join_if_exists(good_installed_path, try_launch_scripts)
    if not start_script or self_install_options['exists_action'] != "skip":
        app._download_page()
        installed = app.download_first(event_template=self_install_options)
        # ^ installed *hierosoft*
        # ^ merely calls self.d_click(evt) on first meta
        #   in self.link_metas (not self.installed_metas)
        # ^ enable_install runs (checked in _on_archive_ready)
        #   as long as cb_done isn't overridden by a cb_done arg.
        # install_archive(archive_path, evt=meta)
    else:
        echo0("--upgrade was not specified. Using existing %s"
              % pformat(good_installed_path))
        installed = copy.deepcopy(self_install_options)
        if "installed_path" not in installed:
            installed['installed_path'] = good_installed_path
        else:
            echo0("Warning: using specified installed_path: %s"
                  % installed['installed_path'])

    error = installed.get('error')
    if error:
        app.set_status(error)
        raise RuntimeError(prefix+"download & install launcher failed: %s"
                           % error)

    installed_path = installed.get('installed_path')
    if installed.get("already_installed"):
        echo0("Already installed: %s"
              % pformat(installed_path))
    if not installed_path:
        echo0("d_click called by download_first must set"
              " 'installed_path' before *every* return unless"
              " 'error' is set. Ultimately, install_folder"
              " (or potentially _on_archive_ready)"
              " has to set it if install_archive is called.")
        # fault-tolerant way:
        installed_path = good_installed_path
    start_script = join_if_exists(installed_path, try_launch_scripts)
    if start_script is None:
        raise FileNotFoundError(
            "Any of %s in %s" % (try_launch_scripts, installed_path)
        )
    import subprocess
    launcher_cmd = [app.best_python, start_script]

    _ = subprocess.Popen(
        launcher_cmd,
        start_new_session=True,
        cwd=installed_path,
    )
    # ^ start_new_session allows the binary launcher to close
    #   and be replaced by the Python copy
    root.mainloop()
    # Keep splash a moment, not scare user with flashing screen:
    # time.sleep(2)

    def close():
        root.destroy()
    root.after(2, close)
    return 0


if __name__ == "__main__":
    try:
        if sys.version_info.major >= 3:  # try:
            from tkinter import messagebox
            from tkinter import filedialog
            from tkinter import simpledialog
            # ^ such as name = simpledialog.askstring('Name',
            #                                         'What is your name?')
            import tkinter as tk
            import tkinter.font as tkFont
            from tkinter import ttk
            # from tkinter import tix
        else:  # except ImportError:
            # Python 2
            import tkMessageBox as messagebox
            import tkFileDialog as filedialog
            import tkSimpleDialog as simpledialog
            import Tkinter as tk
            import tkFont
            import ttk
            # import Tix as tix
        enable_tk = True
    except ImportError as ex:
        echo0("Error: You must install python3-tk")
        sys.exit(1)
    sys.exit(main())
