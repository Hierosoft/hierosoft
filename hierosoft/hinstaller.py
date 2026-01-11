# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division

from collections import OrderedDict
import json
import os
import platform
import shlex
import shutil
import sys
import time
# import uuid
import zipfile

from hierosoft.moreplatform import (
    install_shortcut,
    get_dir_size,
)

import hierosoft

from hierosoft import (
    echo0,
    # write0,
    sysdirs,
)

from hierosoft.moreplatform import (
    # get_digest,
    get_hexdigest,
    zip_dir,
)

from hierosoft.morelogging import (
    utcnow,
)

def best_timer_ms():
    return time.time_ns() / 1000000


def best_timer_sec():
    return time.time_ns() / 1000000000


# if sys.version_info.major < 3:
#     def best_timer_ms():
#         ns = time.time_ns()
#         ms = ns // 1000000
#         if ns % 1000000 >= 50000:
#             # Use the modulus for rounding
#             ms += 1
#         return ms
#     def best_timer_sec():
#         return float(best_timer_ms()) / 1000.0


def console_callback(evt):
    count = evt.get('done_bytes')
    total = evt.get('total_bytes')
    sys.stderr.write("\r")
    if total and total > 0 and count:
        ratio = float(count) / float(total)
        sys.stderr.write(
            "{}/{} ({}%) ".format(count, total, round(ratio*100, 1))
        )
    error = evt.get('error')
    message = evt.get('message')
    if error:
        sys.stderr.write("[console_callback] "+error)
    elif message:
        sys.stderr.write("[console_callback] "+message)
    sys.stderr.flush()
    if evt.get('status') == "done":
        sys.stderr.write("\n")
        sys.stderr.flush()


class HInstaller:
    """Manage an install process on any platform.

    Args:
        src_root (str): The extracted install source directory.
        dst_root (str): The destination program directory for install.
        undo (file, optional): An open uninstall script file. Defaults
            to None.
        redo (file, optional): An open log file. Defaults to None.
        meta (dict): Settings for the program installation:
            - 'keeps' (list[str], optional): A list of files and/or
              directories to leave intact if in dst. Each must be
              relative to src (and not start with "/", nor start with
              backslash nor "{}:" on Windows where {} is a letter)!

    Attributes:
        undo_root (Optional[str]): Where to place deleted files

    Raises:
        ValueError: Blank value or absolute path in keeps
        ValueError: Invalid src or dst (drive or special folder)
    """
    def __init__(self, src_root, dst_root, meta):
        self.finalized = False
        self.started = False
        self.simulate = True
        self.last_update_sec = None
        self.finalized_simulated = False
        self.luid_meta_dir = None
        self.undo_root = None
        # self.parent_estimates = OrderedDict()
        # self.estimates = OrderedDict()
        self.delete_bytes_total = 0

        roots = {
            'src': src_root,
            'dst': dst_root,
        }
        del src_root
        del dst_root
        for key, path in roots.items():
            if not path:
                raise ValueError('Blank {}: "{}"'.format(key, path))
            if path.endswith(os.path.sep):
                if path in ("/", "\\"):
                    # Do not allow the root directory for either!
                    raise ValueError('Invalid (cannot use root dir) {}: "{}"'
                                     ''.format(key, path))
                roots[key] = roots[key][:-1]
            if platform.system() == "Windows":
                if (len(path) == 2) and (path[1] == ":"):
                    raise ValueError('Cannot use drive ("{}") as {}!'
                                     ' You must use a subfolder instead.'
                                     ''.format(path, key))
            for c_key, c_path in sysdirs.items():
                if roots[key].lower() == c_path.lower():
                    raise ValueError('Cannot use {} ("{}") as {}!'
                                     ' You must use a subfolder instead.'
                                     ''.format(c_key, path, key))
            if not roots[key]:
                raise ValueError('Invalid {}: "{}"'.format(key, roots[key]))
        self.meta = meta
        self.issues = []
        keeps = self.meta.get('keeps')
        if keeps:
            for i in range(len(keeps)):
                if len(keeps[i]) < 1:
                    raise ValueError("Blank value in keeps.")
                bad = False
                if platform.system() == "Windows":
                    if ((len(keeps) >= 2 and keeps[1] == ":")
                            or (keeps[0] == "\\")):
                        bad = True
                else:
                    if keeps[0] == "/":
                        bad = True
                if bad:
                    raise ValueError('Absolute paths are not accepted for'
                                     ' keeps. Each must be relative to the'
                                     ' install source dir but one was "{}"'
                                     ''.format(keeps[i]))
                if keeps[0].endswith(os.path.sep):
                    keeps[0] = keeps[0][:-1]
            if 'version_path' not in meta:
                echo0("Warning: no 'version_path',"
                      " so no release.txt file will be installed.")
        else:
            self.meta['keeps'] = []
        self.src_root = roots['src']
        self.dst_root = roots['dst']
        self.keeps = keeps
        self.rmdir_lines = None
        self.undo_zip = None

    @property
    def src_root_slash(self):
        if self.src_root.endswith(os.path.sep):
            return self.src_root
        return self.src_root + os.path.sep

    @property
    def dst_root_slash(self):
        if self.dst_root.endswith(os.path.sep):
            return self.dst_root
        return self.dst_root + os.path.sep

    def install(self, callback=None, evt=None):
        """Install the program.

        Uses self.meta['organization'] as parent dir for luid and
        version dirs.

        Args:
            callback (Optional[callable]): If not None, must accept
                a dictionary with various metadata. If 'error' is
                set, assume a failure. Defaults to None.
            evt (Optional[str]): Template for events sent to callback
                (also returned such as for synchronous operation).

        Returns:
            dict: same dict sent to callback if, with ['status'] = "done"
        """
        luid = self.meta.get('luid')
        if not luid:
            raise ValueError("luid is missing (not in meta)."
                             " It should be a unix-like project name"
                             " to use as unique program id.")
        if callback is None:
            callback = console_callback
        self.callback = callback
        start_dt = utcnow()
        install_meta = {}
        install_meta['install_date'] = hierosoft.dt_str(start_dt)
        self.meta['install_date'] = install_meta['install_date']

        # install_uuid = uuid.uuid1()
        # install_id = "{}".format(install_uuid)
        # ^ such as '1a823842-bd7c-11ee-bb4a-58112276c1e6'
        install_id = hierosoft.dt_path_str(start_dt)

        self.luid_meta_dir = hierosoft.appstates_dir(
            self.meta['organization'],
            luid,
            "current",
        )

        # TODO: Use apps_dir for program itself...
        # self.dst = hierosoft.apps_dir(
        #     self.meta['organization'],
        #     luid,
        #     "current",
        # )

        install_ids_path = os.path.join(
            self.luid_meta_dir,
            "installs",
        )
        self.undo_root = os.path.join(install_ids_path, install_id)
        if not os.path.isdir(self.undo_root):
            os.makedirs(self.undo_root)
        if os.path.isdir(self.dst_root):
            echo0('* Setting undo dir for "{}" to "{}"'
                  ''.format(self.dst_root, self.undo_root))

        self.dst_id_file = self.undo_root + ".json"
        self.dst_pending_id_file = self.dst_id_file + ".wip"
        self.bak_id_file = self.dst_id_file + ".bak"

        self.meta['install_id'] = install_id
        # install_meta = self.undo_root + ".json"
        with open(self.dst_pending_id_file, 'w') as meta_file:
            json.dump(self.meta, meta_file, indent=2, sort_keys=True)
        install_log = self.undo_root + ".log"
        uninstall_script = self.undo_root + "-uninstall.sh"
        self.meta['uninstall_script'] = uninstall_script
        self.undo_zip = None
        self.undo_arc_path = os.path.join(self.undo_root, "removed.zip")
        with open(install_log, 'w') as redo:
            with open(uninstall_script, 'w') as undo:
                with zipfile.ZipFile(self.undo_arc_path, 'w') as self.undo_zip:
                    result = self._install(
                        undo=undo,
                        redo=redo,
                        callback=callback,
                        evt=evt,
                    )
        if 'size' not in self.meta:
            self.meta['size'] = self.bytes_total
        else:
            # It must be an upgrade, so calculate delta
            delta = self.bytes_total - self.delete_bytes_total
            self.meta['size'] = self.meta['size'] + delta
        # if not result.get('error'):
        if self.deletes_total < 1:
            # There were no files to backup, so delete backup archive
            # (even if simulate since it is a zip of files to delete):
            os.remove(self.undo_arc_path)
        # Do *not* run after_install until *2nd* run (simulate=False)
        return result

    def _install(self, undo=None, redo=None, evt=None, simulate=True,
                 callback=None):
        '''
        See "install" method documentation for more information.

        Requires:
            self.callback (Callable): Method accepting dict for progress
                and ['status']="done" on last callback.

        Args:
            undo (Optional[file]): A file-like object which must
                be open if undo_root. The resulting script can be used to
                undo the operation. However, deleted files can only be
                undone if `undo_root` is set (Otherwise, such lines will be
                commented with '#').
            redo (Optional[file]): A file-like object which must be
                open if undo_root.
            simulate (bool, optional): Skip actual file operations (only
                write install script). Defaults to True!
        '''

        if self.started:
            raise RuntimeError("_install can only run once per session.")

        if evt is None:
            evt = {}
        if evt.get('status') == "done":
            raise ValueError('evt["status"] is already "done"')
        if evt.get('error'):
            raise ValueError('evt["error"] is already "{}"'
                             ''.format(evt.get('error')))
        self.delete_bytes_total = 0  # reset each time since
        #  size (of delete) doesn't matter for calculating progress
        self.bytes_done = 0
        self.deletes_done = 0
        self.last_update_sec = None
        self.match_count = 0
        self.add_count = 0
        self.file_count = 0
        if simulate:
            self.matches = set()
            self.bytes_total = 0
            self.deletes_total = 0  # file count (*not* byte count)
            if evt.get('bytes_done'):
                raise ValueError('bytes_done was already {}'
                                 ''.format(evt.get('bytes_done')))
        else:
            if not self.hasattr(self, 'matches'):
                self.matches = set()
            self.started = True
            self.ended = False
            if evt.get('bytes_total'):
                raise ValueError('bytes_total was already {}'
                                 ''.format(evt.get('bytes_total')))

        self.undo = undo
        self.redo = redo
        self.simulate = simulate
        self.callback = callback

        result_path = None
        warning = None
        src = self.src_root
        dst = self.dst_root
        # undo_dir = self.undo_root

        self.rmdir_lines = []  # used to sort & delay write to ensure removal
        # Unlike rmdir, mkdir doesn't need to be sorted, only need to be unique
        self.mkdir_lines = set()
        self.undo_mkdir_lines = set()

        evt['tmp'] = {}
        # if not os.path.isdir(dst):
        #     self.copytree(src, dst)
        # else:

        # src_files was already checked.

        # ^ Since merge is the default sync method, maybe delete
        #   certain subs first?

        # adds = (  # only add subs if not existing on dest!
        #     'cache',
        #     # os.path.join("clientmods", "preview"),
        # )
        # overwrites = []
        # ^ max 32-bit signed int is ~ 1.9999 Gigabytes if unit is bytes
        if simulate:
            callback({'message': "Estimating size..."})

        # self.copytree(src, dst)

        evt.update({
            'bytes_done': self.bytes_done,
            'bytes_total': self.bytes_total,
        })
        results = self.copytree(src, dst, callback=callback, evt=evt)
        if results.get('error'):
            evt.update(results)
            callback(evt)
            evt['status'] = "done"
            return evt

        # Leave result_path as None

        if result_path:
            version_path = self.meta.get('version_path')
            if version_path and os.path.isfile(version_path):
                version_name = os.path.basename(version_path)
                # shutil.copy(
                file_results = self.install_file(
                    version_path,
                    os.path.join(dst, version_name),
                    any_source=True,
                    evt=evt,
                )
                error = file_results.get('error')
                if error:
                    evt['status'] = "done"
                    callback(evt)
                    return evt
            echo0("Done")

        for exec_relpath in self.meta['shortcut_exe_relpaths']:
            exec = os.path.join(dst, exec_relpath)
            if 'shortcut' not in self.meta:
                self.meta['shortcut'] = {}
            self.meta['shortcut']['Path'] = os.path.dirname(exec)
            sc_results = install_shortcut(exec, dst, self.meta)
            sc_warning = sc_results.get('warning')
            if sc_warning is not None:
                if warning is not None:
                    warning += "; " + sc_warning
                else:
                    warning = sc_warning
        evt.update({
            'dst': dst,
            'warning': warning,
            'status': "done",
        })

        callback(evt)
        return evt

    def increment_removed(self, count=1, byte_count=None, evt=None):
        """Update either deletes_total or deletes_done depending on simulate
        (counts files, *not* bytes).

        Args:
            count (int, optional): How many files were affected.
                Defaults to 1.
            evt (dict, optional): dict to update using update_event.
                Defaults to None.
        """
        if self.simulate:
            self.deletes_total += count
        else:
            self.deletes_done += count
        if evt:
            self.update_event(evt, "delete")
        if byte_count is not None:
            self.delete_bytes_total += byte_count

    def increment_size(self, byte_count, evt=None, count=1):
        """Update either bytes_total or bytes_done depending on self.simulate

        Args:
            byte_count (int): How many bytes to add
            evt (dict, optional): dict to update using update_event.
                Defaults to None.
        """
        self.add_count += count
        if self.simulate:
            self.bytes_total += byte_count
        else:
            self.bytes_done += byte_count
        if evt:
            self.update_event(evt, "bytes")

    def get_removed(self):
        return self.deletes_total if self.simulate else self.deletes_done

    def get_size(self):
        return self.bytes_total if self.simulate else self.bytes_done

    def update_event(self, evt, mode):
        if mode == "bytes":
            evt.update({
                'bytes_done': self.bytes_done,
                'bytes_total': self.bytes_total,
            })
        elif mode == "delete":
            evt.update({
                'deletes_done': self.deletes_done,
                'deletes_total': self.deletes_total,
            })
        else:
            raise ValueError('"size" or "delete" was expected for mode')
        return evt

    def install_file(self, src_path, dst_path, allow_external_src=False,
                     allow_external_dst=False, evt=None):
        '''Handle a directory listing during install.
        This must be compatible with the "ignore" option of
        shutil.copytree

        The src_path and dst_path are permissive in case files from
        other places such as generated shortcuts need to be installed.

        Example: shutil.copytree(src, dst,
        copy_function=npinstaller.install_file,
        ignore=npinstaller.on_install_dir)

        Args:
            src_path (str): The full source file path to install.
            dst_path (str): The full destination file path.
            allow_external_src (Optional[bool]): Whether to allow
                installing files not in self.src_root
        '''
        cmd = "cp"
        path1 = src_path
        args = "-f"
        if os.path.islink(src_path):
            # path1 = os.readlink(src_path)
            # cmd = "ln"
            # args = "--preserve=links"
            # ^ not for dirs. See comments on <https://superuser.com/a/138592>.
            args = '-fa'
            # ^ do not do a, since it preserves ownership ??
        self.append_install(shlex.join([
            cmd,
            args,
            path1,
            dst_path
        ]))
        if not self.simulate:
            shutil.copy2(src_path, dst_path, follow_symlinks=False)
            # follow_symlinks=False copies symlinks as symlinks
        self.increment_size(os.path.getsize(src_path), evt=evt)
        # if callback:
        #     callback(evt)

        self.append_undo(shlex.join([
            "rm",
            "-f",
            dst_path
        ]))

    # def _copytree(self, src_root, dst_root, sub, symlinks=True, ignore=None,
    #               copy_function=None, ignore_dangling_symlinks=False,
    #               dirs_exist_ok=False):
    #     src = os.path.join(src_root, sub)
    #     dst = os.path.join(dst_root, sub)

    def append_install(self, line):
        if not line.endswith("\n"):
            line += "\n"
        self.redo.write(line)
        self.redo.flush()

    def append_undo(self, line):
        if not line.endswith("\n"):
            line += "\n"
        self.undo.write(line)
        self.undo.flush()

    def get_op_vars(self, src_root, dst_root, rel=None,
                    allow_external_src=False, allow_external_dst=False,
                    symlinks=True):
        """Get a reason why the file should be skipped, if any.

        Args:
            src_root (str): Either self.src_root or a full path (in that
                case rel must be None, and dst_root must be a full path).
            dst_root (str): Either self.dst_root or a full path (in that
                case rel must be None, and src_root must be a full path).
            rel (str, optional): Path relative to src_root and dst_root.
                If they are full paths, this must be None. Defaults to
                None.
            allow_external_src (bool, optional): Allow src_root to be a
                full path not in self.src_root. True requires rel=None.
                Defaults to False.
            allow_external_dst (bool, optional): Allow dst_root to be a
                full path not in self.src_root. True requires rel=None.
                Defaults to False.
            symlinks (bool, optional): copy symlinks. Defaults to True
                (shutil's defaults to False).

        Raises:
            ValueError: _description_
            ValueError: _description_

        Returns:
            dict: Description of issue if any.
                - 'mode' (str): If "skip" then the directory should be skipped.
                - 'warning' (str): If set, then this should be shown at
                  the end of simulation and confirmed by the user before
                  install.
                - 'error' (str): If set, the real install should *not*
                  *not* proceed after simulation!

        """
        keeps = self.meta.get('keeps') or []
        replaces = self.meta.get('replaces') or []
        vars = OrderedDict()

        vars['src_rel'] = rel
        vars['dst_rel'] = rel
        vars['src_root_slash'] = self.src_root_slash
        vars['dst_root_slash'] = self.dst_root_slash
        vars['allow_external_src'] = allow_external_src
        vars['allow_external_dst'] = allow_external_dst

        if rel is None:
            vars['src_path'] = src_root
            vars['dst_path'] = dst_root
            for place in ('src', 'dst'):
                if vars[place+'_path'].startswith(vars[place+'_root_slash']):
                    vars[place+'_rel'] = \
                        vars[place+'_path'][len(vars[place+'_root_slash']):]
                else:
                    vars[place+'_rel'] = vars[place+'_path']
                    # Do not set *_root_slash until after shown if error
                    if not vars['allow_external_'+place]:
                        vars['error'] = (
                            'is not in {}_root "{}"'
                            ' (and allow_external_{} is {})'
                            ''.format(place, vars[place+'_root_slash'],
                                      place, vars['allow_external_'+place])
                        )
                        # *_path is already set.
                        vars['mode'] = "skip"
                        return vars
                    vars[place+'_root_slash'] = ""
        else:
            if src_root != self.src_root:
                vars['error'] = ('is not src_root, but rel was set ("{}").'
                                 ''.format(rel))
                # src_path is already set
                return vars
            if dst_root != self.dst_root:
                vars['error'] = ('is not dst_root, but rel was set ("{}").'
                                 ''.format(rel))
                # *_path is already set
                return vars

            vars['src_path'] = os.path.join(src_root, vars['src_rel'])
            vars['dst_path'] = os.path.join(dst_root, vars['dst_rel'])
            if not os.path.exists(vars['src_path']):
                vars['error'] = 'missing'
                # *_path is already set
                return vars
        del rel
        # rel = src_rel
        if os.path.isfile('src_path'):
            self.file_count += 1
        if os.path.exists(vars['dst_path']):
            if vars['src_rel'] in keeps:
                vars['mode'] = "skip"
                vars['warning'] = 'will not be overwritten'
            elif (not symlinks) and os.path.islink(vars['src_path']):
                vars['mode'] = "skip"
                vars['warning'] = 'is a symlink (skipped)'
            elif (os.path.islink(vars['dst_path'])
                    and not os.path.islink(vars['src_path'])):
                vars.update({
                    'warning': "destination is a symlink not source (skipped)",
                    'mode': "skip",
                })
            elif vars['src_rel'] in replaces:
                vars['mode'] = 'delete'

            if os.path.isfile(vars['src_path']):
                vars['src_size'] = os.path.getsize(vars['src_path'])
                if os.path.isdir(vars['dst_path']):
                    vars['mode'] = 'delete'
                    vars['warning'] = 'is file on src and dir on dest!'
            else:
                if os.path.isfile(vars['dst_path']):
                    vars['mode'] = 'delete'
                    vars['warning'] = 'is dir on src and file on dest!'

            if vars.get('mode') != "skip":
                if (os.path.isfile(vars['src_path'])
                        and os.path.isfile(vars['dst_path'])
                        and not os.path.islink(vars['src_path'])):
                    if vars['dst_rel'] not in self.matches:
                        src_size = os.path.getsize(vars['src_path'])
                        dst_size = os.path.getsize(vars['dst_path'])
                        # src_ts = os.path.getmtime(vars['src_path'])
                        # dst_ts = os.path.getmtime(vars['dst_path'])
                        # ^ varies (extraction changes time)
                        # src_time = time.ctime(src_ts)
                        # src_dt = datetime.fromtimestamp(src_ts)
                        # ct is ctime, as in datetime.from
                        src_hash = get_hexdigest(vars['src_path'])
                        dst_hash = get_hexdigest(vars['dst_path'])
                    else:
                        # force a match (simulate mode already matched it)
                        src_size = None
                        dst_size = None
                        src_hash = None
                        dst_hash = None
                    if (src_size == dst_size) and (src_hash == dst_hash):
                        # and (src_ts == dst_ts):
                        if self.simulate:
                            self.matches.add(vars['dst_rel'])
                        vars['mode'] = "skip"
                        vars['hide'] = True
                        self.match_count += 1
                        if 'warning' in vars:
                            del vars['warning']
                        # vars['src_ts'] = src_ts
                        # vars['dst_ts'] = dst_ts
        return vars

    def copytree(self, src_root, dst_root, rel=None, symlinks=True,
                 ignore=None, copy_function=None,
                 ignore_dangling_symlinks=False, dirs_exist_ok=True,
                 callback=None, evt=None, depth=0):
        """Copy a tree with conditions regarding existing files.
        Behavior is modified by:
        - self.meta['keeps'] (list[str]): do nothing if exists
        - self.meta['replaces'] (list[str]): delete files in dest if not
          in src

        Args:
            src_root (str): The top-level install source path.
            dst_root (str): The top-level install destination path.
            rel (str, optional): The sub-path under root (for both src
                and dst). If None, then roots will be used.
            ignore (_type_, optional): _description_. Defaults to None.
            copy_function (_type_, optional): _description_. Defaults to
                self.install_file *which respects 'replaces' and 'keeps'
                in self.meta* (shutil's defaults to shutil.copy2).
                - must accept 'evt' dict keyword argument (unlike copy2)
                  that is a dict template for updating progress.
            ignore_dangling_symlinks (bool, optional): _description_.
                Defaults to True (shutil's defaults to False).
            dirs_exist_ok (bool, optional): Do not raise exception if
                any dest dir exists. Defaults to False.
        """
        # shutil.copytree(src, dst, symlinks=symlinks,
        #                 ignore=self.on_install_dir,
        #                 copy_function=self.install_file,
        #                 ignore_dangling_symlinks=ignore_dangling_symlinks,
        #                 dirs_exist_ok=dirs_exist_ok)
        if copy_function is None:
            copy_function = self.install_file
        # if ignore is None:
        #     ignore = self.on_install_dir
        if callback is None:
            callback = self.callback

        replaces = self.meta.get('replaces') or []

        src_parent_path = src_root
        dst_parent_path = dst_root
        if rel:
            src_parent_path = os.path.join(src_root, rel)
            dst_parent_path = os.path.join(dst_root, rel)

        file_count = 0
        dir_count = 0
        folder_size = 0

        update_delay = 0.5  # seconds

        for sub in os.listdir(src_parent_path):
            sub_rel = sub
            if rel is not None:
                sub_rel = os.path.join(rel, sub)
            mode = "add"
            src_path = os.path.join(src_root, sub_rel)
            dst_path = os.path.join(dst_root, sub_rel)

            if sub_rel in replaces:
                # - Recursion doesn't overlap: only runs when in
                #   `replaces`
                # - Delete is *not* necessary for dst_root--That may be
                #   overkill (various user files, generated files, &
                #   release.txt may be there).

                # _evt, _deleted =
                self.delete_not_in_src(
                    src_parent_path,
                    dst_parent_path,
                    sub,
                    depth=depth+1,
                    delete0=True,
                    allow_external_src=False,
                    allow_external_dst=False,
                    evt=evt,
                    callback=callback,
                )

            if ((self.last_update_sec is None)
                    or (best_timer_sec() - self.last_update_sec
                        > update_delay)):
                callback(evt)  # auto-updated by self.increment_*
                self.last_update_sec = best_timer_sec()
            vars = self.get_op_vars(
                src_root,
                dst_root,
                sub_rel,
                # allow_external_src=False,
                # allow_external_dst=False,
                symlinks=symlinks,
            )
            mode = vars.get('mode')
            evt.update(vars)
            if vars.get('error'):
                callback(vars)
                return evt
            if vars.get('warning'):
                if not self.finalized_simulated:
                    self.issues.append(vars)
            pre = ""
            if vars.get('hide'):
                # Do not log, copy, nor recurse.
                continue
            elif mode == "skip":
                # ^ get_op_vars already already wrote a log line.
                pre = "# "
                cmd = "cp"
                args = '-f'
                msg = vars.get('error')
                if not msg:
                    msg = vars.get('warning')
                if not msg:
                    msg = vars.get('info')
                if msg:
                    msg = msg.replace("\r\n",
                                      "  ").replace("\n",
                                                    "  ").replace("\r", "  ")

                path1 = vars['src_path']
                if os.path.isdir(vars['src_path']):
                    cmd = "rsync"
                    args = '-rtv'
                    path1 += "/"
                if os.path.islink(src_path):
                    cmd = "ln"
                    args = "-s"
                    path1 = os.readlink(src_path)
                self.append_install(pre+shlex.join([
                    cmd,
                    args,
                    path1,
                    vars['dst_path'],
                ])+'  # {}'.format(msg))
                # Do *not* call self.increment_size
                continue

            if os.path.isfile(src_path):
                prev_done = self.get_size()
                copy_function(src_path, dst_path, evt=evt)
                folder_size += self.get_size() - prev_done

                # ^ writes redo line, and if copies (or simulation), undo line
                file_count += 1
                continue
            self.copytree(src_root, dst_root, sub_rel, symlinks=symlinks,
                          ignore=ignore, copy_function=copy_function,
                          ignore_dangling_symlinks=ignore_dangling_symlinks,
                          dirs_exist_ok=dirs_exist_ok, callback=callback,
                          evt=evt, depth=depth+1)

        # self.estimates[rel] = folder_size
        return evt
        # self

    def after_install(self):
        '''Finalize logs.
        - Write self.rmdir_lines (saved via install_file), longest first.
        '''
        if self.finalized:
            raise ValueError("Install was already finalized.")
        if not self.simulate:
            self.finalized = True
        else:
            self.finalized_simulated = True
        # TODO: show self.issues ('warning' or 'error'
        #   and 'dst_path' or 'src_path')
        if self.simulate:
            echo0("Simulation is complete.")
        else:
            echo0("Install is complete.")
        undo = self.undo
        rmdir_lines = list(sorted(self.rmdir_lines, key=len))
        for i in range(len(rmdir_lines)):
            if not rmdir_lines[i].endswith("\n"):
                echo0("Warning: No newline after '{}'".format(rmdir_lines[i]))
                rmdir_lines[i] += "\n"
        for rmdir_line in reversed(rmdir_lines):
            # Remove longest paths first to try to empty parent to allow rmdir.
            undo.write(rmdir_line)  # must *already* include \n
        undo.flush()
        if not self.simulate:
            if os.path.isfile(self.dst_id_file):
                shutil.move(self.dst_id_file, self.bak_id_file)
            shutil.move(self.dst_pending_id_file, self.dst_id_file)
            if os.path.isfile(self.bak_id_file):
                # os.remove(self.bak_id_file)
                _, name = os.path.split(self.bak_id_file)
                shutil.move(self.bak_id_file,
                            os.path.join(self.undo_root, name))
        else:
            pass
            # if os.path.isfile(self.dst_pending_id_file):
            #     os.remove(self.dst_pending_id_file)

    def delete_not_in_src(self, src_parent, dst_parent, sub, depth=0,
                          delete0=True, evt=None,
                          callback=None, allow_external_src=True,
                          allow_external_dst=True):
        if ((src_parent != self.src_root)
                and not src_parent.startswith(self.src_root_slash)):
            if not allow_external_src:
                raise ValueError("sync")
        return self._delete_not_in_src(src_parent, dst_parent, sub,
                                       depth=depth,
                                       delete0=delete0,
                                       evt=evt, callback=callback)

    def _delete_not_in_src(self, src_parent, dst_parent, sub, depth=0,
                           delete0=True, evt=None,
                           callback=None):
        """Delete files/dirs in dest *only if* not in src.

        Remember to add all args *above* to recursive call(s)!

        If self.simulate, self.delete_count is incremented but no file
        operations should be done.

        Args:
            depth (Optional[int]): The depth of the operation--leave this
                alone and it will be managed automatically. All levels
                except 0 (or including 0 if delete0) that are
                directories and are empty will be removed if not in src.
                Defaults to 0.
            delete0 (Optional[bool]): Delete dst if not in src
                even if dst is the caller-specified (top) directory.
            evt (Optional[str]): Template for events sent to callback
                (also returned such as for synchronous operation).
            callback (Optional[callable]): If not None, must accept
                a dictionary with various metadata. If 'error' is
                set, assume a failure. Reserved for future use.

        Returns:
            tuple (evt, int): event dict, and deleted 0 or 1 (1 if sub deleted)
        """
        # a.k.a. delete_if (see alternate one elsewhere)
        # if os.path.sep in sub:
        #     raise ValueError('The sub must be the file/dir name not path:'
        #                      ' "{}"'.format(sub))
        undo = self.undo
        redo = self.redo
        # undo_root = self.undo_dir
        # undo_dir = None
        undo_parent_rel = "system"

        dst = os.path.join(dst_parent, sub)
        src = os.path.join(src_parent, sub)

        if dst.startswith(self.dst_root_slash):
            undo_parent_rel = "program"
            sub_rel = dst[len(self.dst_root_slash):]
        elif dst == self.dst_root:
            undo_parent_rel = "program"
            sub_rel = ""
        else:
            # it is an absolute path, so make up a relative path
            # (ok since goes in "system" not "program")
            sub_rel = dst
            if platform.system() == "Windows":
                if len(sub_rel) > 2 and sub_rel[1] == ":":
                    sub_rel = sub_rel[0] + sub_rel[2:]
                    # ^ use subdir such as C\users under undo_parent_rel
                    #   (Remove colon to make C folder)
        while sub_rel.startswith(os.path.sep):
            # Remove / or \\ (prevents relative os.path.join)
            sub_rel = sub_rel[1:]
        # if undo_root:
        #     undo_dir = os.path.join(undo_root, undo_parent_rel, sub_rel)
        undo_zip_sub = os.path.join(undo_parent_rel, sub_rel)

        if callback is None:
            callback = console_callback
        count = 0
        if evt is None:
            evt = {}
        if self.undo_zip:
            if not undo or undo.closed:
                raise ValueError(
                    "undo (uninstall script) must be open if using undo_dir"
                )
            if not redo or redo.closed:
                raise ValueError(
                    "redo (install log) must be open if using undo_dir"
                )
        if evt.get('tmp') is None:
            evt['tmp'] = {}
        if evt['tmp'].get('md_lines') is None:
            evt['tmp']['md_lines'] = set()
        deleted = 0
        if os.path.isfile(dst):
            # if os.path.islink(dst_path):
            #     link_dst = os.readlink(dst_path)
            if not os.path.isfile(src):
                self.append_install(shlex.join([
                    "rm",
                    "-f",
                    dst
                ]))
                byte_count = os.path.getsize(dst)
                self.increment_removed(byte_count=byte_count, evt=evt)
                # if undo_dir:
                #     # if un_path, undo_dir is already set
                #     move = True
                # else:
                if not self.simulate:
                    if self.undo_zip:
                        self.undo_zip.write(
                            dst,
                            os.path.join(undo_zip_sub)
                        )
                    os.remove(dst)
                deleted += 1
            # if not move:
            # evt['this_count'] = deleted
            return evt, deleted

        for subsub in os.listdir(dst):
            count += 1
            src_path = os.path.join(src, subsub)
            dst_path = os.path.join(dst, subsub)
            subsub_rel = os.path.join(sub, subsub)
            # un_path = None
            # link_dst = None
            # move = False
            # if undo_dir:
            #     un_path = os.path.join(undo_dir, subsub)
            if os.path.isfile(dst_path):
                _, _del = self._delete_not_in_src(src, dst, subsub,
                                                  depth=depth+1,
                                                  delete0=delete0, evt=evt,
                                                  callback=callback)
                count -= _del
                del _
                del _del
                continue
            if not os.path.isdir(src_path):
                # is dir & not on src.
                # if ((undo_dir not in self.undo_mkdir_lines)
                #         and not os.isdir(undo_dir)):
                #     # Make *parent*
                #     if not self.simulate:
                #         os.makedirs(undo_dir)
                #     self.undo_mkdir_lines.add(undo_dir)

                if not os.path.islink(dst_path):
                    self.append_install(shlex.join([
                        "rm",
                        "-rf",
                        dst_path
                    ]))
                    # if not undo_dir:
                    byte_count = 0
                    byte_count = get_dir_size(dst_path)
                    self.increment_removed(
                        count=zip_dir(self.undo_zip, dst_path, undo_zip_sub,
                                      simulate=self.simulate),
                        evt=evt,
                        byte_count=byte_count,
                    )
                    if not self.simulate:
                        shutil.rmtree(dst_path)
                    # else:
                    #     move = True
                else:
                    # is link
                    self.append_install(shlex.join([
                        "rm",
                        "-f",
                        dst_path
                    ]))
                    link_dst = os.readlink(dst_path)
                    # if not undo_dir:
                    self.increment_removed(evt=evt)
                    # ^ byte_count=0
                    if not self.simulate:
                        os.unlink(dst_path)
                        # ^ unlink deletes link *not* target
                    # else:
                    #     move = True
                    self.append_undo(shlex.join([
                        "ln",
                        "-s",
                        link_dst,
                        dst_path
                    ]))
                count -= 1
                # if not move:
                continue  # no recursion (no longer exists)!
            _, _del = self._delete_not_in_src(
                src_parent,
                dst_parent,
                subsub_rel,
                depth=depth+1,
                delete0=delete0,
                evt=evt,
                callback=callback,
            )
            # if not os.path.exists(dst_path):
            if _del:
                count -= 1
        if ((count == 0) and (depth > 0 or delete0)
                and not os.path.exists(src)):
            # Remove empty directory *if* not in src & not top level.
            deleted = 1
            if not os.islink(dst):
                self.append_install(shlex.join([
                    "rmdir",
                    dst_path
                ]))
                if not self.simulate:
                    os.rmdir(dst)
                self.increment_removed(evt=evt)
                # ^ byte_count=0
            else:
                if redo:
                    self.append_install(shlex.join([
                        "rm",
                        "-f",
                        dst_path,
                    ])+"  # directory symlink (*not* recursive delete!)")
                if not self.simulate:
                    os.unlink(dst)
                self.increment_removed(evt=evt)
                # ^ byte_count = 0
        # callback(evt)
        # Do not set evt['status'] = "done"
        #   because the caller (usually install_minetest) may not be done!
        return evt, deleted
