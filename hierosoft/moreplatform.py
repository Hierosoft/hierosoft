# -*- coding: utf-8 -*-
from __future__ import print_function
import copy
import os
# import platform
import shutil
import sys
import subprocess
import tarfile
import tempfile
import zipfile

from pprint import pformat
from zipfile import ZipFile

from hierosoft import (
    echo0,
    SHORTCUT_EXT,
    CACHES,
    get_subdir_names,
)

from hierosoft.morebytes import (
    rewrite_conf,
)

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    FileExistsError = IOError

# TODO: if shlex is used, do:
"""
if sys.version_info.major > 3 and sys.version_info.minor > 8:
    shlex_join = shlex.join
else:
    def shlex_join(parts):
        result = ""
        sep = ""
        for part in parts:
            result += sep
            sep = " "
            if (" " in part) or ('"' in part):
                result += '"%s"' % part.replace('"', '\\"')
            else:
                result += part
        return result
    shlex.join = shlex_join
"""

def install_folder(src, dst, event_template=None):
    '''
    Args:
        event_template (Optional[dict]): Set options for this method and
            default metadata for event returned. Keys:
            - 'exists_action': "delete" to remove destination if exists.
              "skip" to do nothing except set evt['installed_path'] and
              evt['already_installed'] if exists.
    '''
    prefix = "[install_folder] "
    remove_dst = False
    skip_dst = False
    exists_action = event_template.get('exists_action')
    programs_dir = os.path.dirname(dst)
    if not os.path.isdir(programs_dir):
        echo0("Warning: creating programs directory %s"
              % pformat(programs_dir))
        os.makedirs(programs_dir)
    if exists_action:
        if exists_action == "delete":
            remove_dst = True
        elif exists_action == "skip":
            skip_dst = True
        else:
            raise NotImplementedError(prefix+"%s is not implemented"
                                      % exists_action)
    if event_template is None:
        evt = {}
    else:
        if 'error' in event_template:
            raise ValueError("Calls continued after error but should not."
                             " Previous error: %s" % event_template['error'])
        evt = copy.deepcopy(event_template)
    if os.path.isdir(dst):
        # Don't remove until zip is sure to be ok!
        if remove_dst:
            shutil.rmtree(dst)
            # If ignore_errors is False (default), either
            #   calls on_error keyword argument if
            #   set, otherwise raises exception.
        else:
            if skip_dst:
                echo0(prefix+"Warning: skipping extract since exists"
                      " and event_template['exists_action'] is skip")
                evt['already_installed'] = True
                evt['installed_path'] = dst
                return evt
            else:
                evt['error'] = ("The destination already exists: %s"
                                % pformat(dst))
                evt['installed_path'] = dst
                return evt
    # shutil.copytree(src, dst, dirs_exist_ok=False,)
    # dirs_exist_ok: Overwrite files in existing dirs.
    #     Defaults to False (raise FileExistsError if dst exists)
    # symlinks (bool): Defaults to False
    # ignore (Union[str, Iterable[str]])
    # copy_function (object):
    # ignore_dangling_symlinks
    evt['installed_path'] = dst
    shutil.move(src, dst)
    return evt


def install_extracted(extracted_path, dst,
                      event_template=None):
    """Install extracted_path, or if has only sub, install that instead.

    For further documentation see install_folder (where src is either
    extracted_path or single subdirectory if only has 1)

    Args:
        extracted_path (str): The path where one or more items were extracted
            from the archive. If only one directory exists in extracted_path,
            that sub_sub_path will be moved to dst. Otherwise, extracted_path
            will be moved to dst.
            - Therefore, extracted_path cannot be a temp folder! You must
              create extracted_path inside of a temp folder if using a temp
              folder, and the call to this method must be within the scope of
              the open tempfile directory.
        event_template (dict): Default values for the event
            dict that is returned. Even keys not used here
            may be important to the caller (the caller may
            use it in a callback)

    Returns:
        dict: Results of the operation (based on event_template if any)
            such as:
            - 'error' (string): Is set on error.
            - 'extracted_name' (string): Only set if
               the archive contains only one directory (that may indicate
               the identity of the program).
    """
    prefix = "[install_extracted] "
    # move = False
    names = get_subdir_names(extracted_path)  # Do *not* use os.listdir:
    #   (listdir may return hidden files making `== 1` fail below!)
    all_names = list(os.listdir(extracted_path))
    if event_template is None:
        evt = {}
    else:
        if 'error' in event_template:
            raise ValueError("Calls continued after error but should not."
                             " Previous error: %s" % event_template['error'])
        evt = copy.deepcopy(event_template)
    if len(names) == 1:
        evt['extracted_name'] = names[0]
        # It is a zipped folder so don't put it under dst
        # move = True
        src = os.path.join(extracted_path, names[0])
        for sub in all_names:
            sub_path = os.path.join(extracted_path, sub)
            if sub_path != src:
                echo0(prefix+"Warning: skipping hidden %s (used %s)"
                      % (sub, src))
    else:
        # It is zipped files from inside a folder, so put under dst
        src = extracted_path
    installed = install_folder(
        src,
        dst,
        event_template=event_template,
    )
    evt.update(installed)
    return evt


def get_tar_mode(archive, event_template):
    """Get the tar format specifier from the filename.
    The return dict's 'tar.mode' key stores the value if is tar.
    Otherwise, the 'error' key is set.
    'archive_name' is set to help identify the program if a
    user-specified program was downloaded (This mimics
    nopackage's behavior so nopackage may not be necessary
    in the future)
    """
    if event_template is None:
        evt = {}
    else:
        if 'error' in event_template:
            raise ValueError("Calls continued after error but should not."
                             " Previous error: %s" % event_template['error'])
        evt = copy.deepcopy(event_template)
    evt['archive_name'], dot_ext = os.path.splitext(archive)
    dot_ext_lower = dot_ext.lower()
    # if archive.lower()[-8:] == ".tar.bz2":
    if dot_ext_lower == ".bz2":
        evt['tar.mode'] = "r:bz2"
    elif dot_ext_lower in [".gz", ".tgz"]:
        evt['tar.mode'] = "r:gz"
    elif dot_ext_lower == ".xz":
        evt['tar.mode'] = "r:xz"
    else:
        evt['error'] = '"%s" has unknown tar extension' % archive
    return evt


def install_tar(archive, dst, remove_archive=False,
                event_template=None):
    """Install a tar-compatible file such as .bz2, .gz, .xz.

    For returns and other documentation, see install_extracted.
    """
    mode_args = get_tar_mode(archive, remove_archive=False,
                             event_template=event_template)
    if 'error' in mode_args:
        return mode_args
    mode = mode_args['tar.mode']
    if event_template is None:
        evt = {}
    else:
        if 'error' in event_template:
            raise ValueError("Calls continued after error but should not."
                             " Previous error: %s" % event_template['error'])
        evt = copy.deepcopy(event_template)
    if not os.path.isfile(archive):
        evt['error'] = "The file doesn't exist: %s" % pformat(archive)
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            extracted_path = os.path.join(tmpdirname, "extracted")
            with tarfile.open(archive, mode) as archive_handle:
                # for i in archive_handle:
                    # archive_handle.extractfile(i)
                archive_handle.extractall(extracted_path)
            installed = install_extracted(
                extracted_path,
                dst,
                event_template=evt,
            )
            if not installed.get('error'):
                if remove_archive:
                    os.remove(archive)
            evt.update(installed)
    except EOFError:
        fmt = mode.split(":")[-1]
        msg = "Incomplete %s archive: %s" % (fmt, archive)
        evt['error'] = msg
        return evt
    # finally:
    #     if archive_handle is not None:
    #         archive_handle.close()
    #         archive_handle = None
    return evt


def install_zip(archive, dst, remove_archive=False,
                event_template=None):
    """Install a zip file. Automatically use subdir from zip if 1 & no file.

    For returns and other documentation, see install_extracted.
    """
    if event_template is None:
        evt = {}
    else:
        if 'error' in event_template:
            raise ValueError("Calls continued after error but should not."
                             " Previous error: %s" % event_template['error'])
        evt = copy.deepcopy(event_template)
    if not os.path.isfile(archive):
        evt['error'] = "The file doesn't exist: %s" % pformat(archive)
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            extracted_path = os.path.join(tmpdirname, "extracted")
            with ZipFile(archive, 'r') as this_zip:
                this_zip.extractall(extracted_path)
            installed = install_extracted(
                extracted_path,
                dst,
                event_template=evt,
            )
            if not installed.get('error'):
                if remove_archive:
                    os.remove(archive)
            evt.update(installed)
    except zipfile.BadZipFile as ex:
        evt['error'] = "%s: %s" % (type(ex).__name__, ex)
        echo0("Error extracting %s: %s" % (pformat(archive), ex))
        delete_msg = "Deleting %s" % pformat(archive)
        evt['error'] += "\n" + delete_msg
        echo0(delete_msg)
        try:
            os.remove(archive)
        except PermissionError as ex:
            permission_msg = "Cannot delete %s. Delete the faulty file manually."
            echo0(permission_msg)
            evt['error'] + "\n" + permission_msg
    return evt


def install_archive(archive, dst, remove_dst=False,
                    remove_archive=True, event_template=None):
    """Extract and install an archive file to dst directory.

    For returns and other documentation, see install_extracted.
    """
    # self.root.update()
    if event_template is None:
        evt = {}
    else:
        if 'error' in event_template:
            raise ValueError("Calls continued after error but should not."
                             " Previous error: %s" % event_template['error'])
        evt = copy.deepcopy(event_template)
    if not archive:
        evt['error'] = "Archive path was not set before install_archive."
        return evt
    tar_args = get_tar_mode(archive, event_template=evt)
    if archive.lower().endswith(".zip"):
        installed = install_zip(
            archive,
            dst,
            remove_archive=remove_archive,
            event_template=evt,
        )
    elif tar_args.get('mode') and not tar_args.get('error'):
        installed = install_tar(
            archive,
            dst,
            remove_archive=remove_archive,
            event_template=evt,
        )
    else:
        evt['error'] = "Unknown archive extension: %s" % pformat(archive)
        installed = evt
    if 'error' not in installed:
        installed['Path'] = dst
    return installed
    # uninstall button & mode removed (too many nested conditions) 20230823
    # TODO: implement uninstall mode & button elsewhere


def make_shortcut(meta, program_name, mgr, push_label=echo0,
                  uninstall=False):
    """Create a shortcut.

    Args:
        meta (dict): data about the program
        program_name (_type_): _description_
        mgr (_type_): _description_
        push_label (_type_, optional): _description_. Defaults to echo0.
        uninstall (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    installed_path = meta['Path']  # *required*--missing from earlier versions
    ret = True
    desktop_path = mgr.get_desktop_path()
    sc_ext = SHORTCUT_EXT
    bin_path = meta.get('Exec')
    action = "create"
    if uninstall:
        action = "uninstall"
    if not uninstall:
        if bin_path is None:
            msg = "installed_bin is missing from meta."
            push_label("{} shortcut failed since".format(action))
            push_label(msg)
            print(msg)
            return False
    print("* {} shortcut...".format(action))
    desktop_sc_name = program_name
    version = meta.get('version')
    sc_src_name = program_name
    if version is not None:
        desktop_sc_name += " " + version + " Nightly"
    sc_label_s = desktop_sc_name[0].upper() + desktop_sc_name[1:]
    if sc_ext != "desktop":
        # filename is visible if not "desktop" format, so capitalize
        desktop_sc_name = sc_label_s
    if len(sc_ext) > 0:
        desktop_sc_name += "." + sc_ext
        sc_src_name += "." + sc_ext
    else:
        print("WARNING: The shortcut extension is unknown for your"
              " platform.")
    desktop_sc_path = os.path.join(desktop_path, desktop_sc_name)

    print("* id: {}".format(meta['luid']))
    if sc_ext == "desktop":
        PREFIX = os.path.join(mgr.profile_path, ".local")
        BIN = os.path.join(PREFIX, "bin")
        sh_path = os.path.join(BIN, "{}-logged.sh".format(program_name))
        logexec = bin_path
        # TODO: Prevent Blender startup crash:
        '''
        ERROR (gpu.shader): gpu_shader_2D_widget_base FragShader:
              |
           81 | layout(depth_any) out float gl_FragDepth;
              |         ^
              | Error: unrecognized layout identifier `depth_any'
        '''
        # on older video
        # cards not supporting OpenGL 4.2 as per
        # <https://developer.blender.org/T98708>:
        # logexec = "MESA_GL_VERSION_OVERRIDE=4.1" + logexec
        #   + ' > ' + CACHE
        #   + '/blender-`date "+%Y-%m-%d"`-gl4.1-error.log 2>&1'
        # MESA_GL_VERSION_OVERRIDE=4.1 /home/owner/Downloads
        #   /blendernightly/versions/3.2.0-stable+v32.e05e1e369187.x86_64-release
        #   /blender > /home/owner/.cache/blender-nightly
        #   /blender-`date "+%Y-%m-%d"`-gl4.1-error.log 2>&1
        CACHE = os.path.join(CACHES, program_name)
        if not os.path.isdir(CACHE):
            os.makedirs(CACHE)
        if bin_path is not None:
            logexec += (' > ' + CACHE
                        + '/{}-error.log 2>&1'.format(program_name))
        if not uninstall:
            with open(sh_path, 'w') as outs:
                outs.write("#!/bin/sh" + "\n")
                outs.write(logexec + "\n")
            os.chmod(sh_path, 0o755)
            print("* wrote {}".format(sh_path))
            if os.path.isfile(desktop_sc_path):
                print("* removing {}".format(desktop_sc_path))
                os.remove(desktop_sc_path)
            print("* writing {}...".format(desktop_sc_path))
            sc_src_path = os.path.join(installed_path, sc_src_name)
            if not os.path.isfile(sc_src_path):
                msg = sc_src_name + " is missing"
                push_label("ERROR: {} shortcut failed since"
                           "".format(action))
                push_label(msg)
                print(msg)
                return False
            rewrite_conf(
                sc_src_path,
                desktop_sc_path,
                {
                    'Name': sc_label_s,
                    'Exec': sh_path,
                    'Path': installed_path,
                },
                allow_adding=True,  # default is True (Add new lines for keys).
            )
            try:
                # Keep the desktop shortcut and mark it executable.
                os.chmod(desktop_sc_path, 0o755)
                # ^ leading 0o denotes octal
            except Exception as ex:
                echo0("Warning: could not mark icon as executable ({})"
                      "".format(ex))
        else:
            pass
            # print("* {} is skipping shortcut writing".format(action))

        PREFIX = os.path.join(mgr.profile_path, ".local")
        SHARE = os.path.join(PREFIX, "share")
        applications_path = os.path.join(SHARE, "applications")
        if not uninstall:
            if not os.path.isdir(applications_path):
                os.makedirs(applications_path)
        sc_name = "org.blender.{}.desktop".format(program_name)
        sc_path = os.path.join(
            applications_path,
            sc_name
        )
        desktop_installer = "xdg-desktop-menu"
        u_cmd_parts = [desktop_installer, "uninstall", sc_path]
        if not uninstall:
            tmp_sc_dir_path = tempfile.mkdtemp()
            tmp_sc_path = os.path.join(tmp_sc_dir_path,
                                       sc_name)
            shutil.copy(desktop_sc_path, tmp_sc_path)
            print("* using {} for {}".format(desktop_sc_path, tmp_sc_path))
            # ^ XDG requires this naming.
        # "--novendor" can force it, but still not if there are spaces.

        # Always remove the old icons first, even if not uninstall:

        if os.path.isfile(desktop_sc_path):
            print("* removing {}...".format(desktop_sc_path))
            os.remove(desktop_sc_path)
        elif uninstall:
            print("* there is no {}...".format(desktop_sc_path))

        if os.path.isfile(sc_path):
            # print("* removing shortcut \"{}\"".format(sc_path))
            # os.remove(desktop_sc_path)
            print("* uninstalling shortcut \"{}\"".format(sc_path))
            subprocess.run(u_cmd_parts)
            # ^ Using only the name also works: sc_name])
            # ^ Using the XDG uninstall subcommand ensures that the
            #   icon in the OS application menu gets updated if the
            #   shortcut was there but different (such as with a
            #   different version number or otherwise different
            #   name).
        elif uninstall:
            print("* there is no {}...".format(sc_path))
        # else:
        #     print("* there's no {}...".format(sc_path))
        if not uninstall:
            sc_cmd_parts = [desktop_installer, "install", tmp_sc_path]
            install_proc = subprocess.run(sc_cmd_parts)
            inst_msg = "OK"
            os.remove(tmp_sc_path)
            if install_proc.returncode != 0:
                inst_msg = "FAILED"
                print("* {}...{}".format(" ".join(sc_cmd_parts),
                                         inst_msg))
                print("  - attempting to copy to {} manually..."
                      "".format(sc_path))
                shutil.copyfile(desktop_sc_path, sc_path)
            else:
                print("* {}...{}".format(" ".join(sc_cmd_parts),
                                         inst_msg))
    elif sc_ext == "bat":
        if not uninstall:
            outs = open(desktop_sc_path, 'w')
            outs.write('"' + bin_path + '"' + "\n")
            outs.close()
        else:
            if os.path.isfile(desktop_sc_path):
                print("* removing {}...".format(desktop_sc_path))
                os.remove(desktop_sc_path)
    elif sc_ext == "command":
        if not uninstall:
            outs = open(desktop_sc_path, 'w')
            outs.write('"' + bin_path + '"' + "\n")
            outs.close()
        else:
            if os.path.isfile(desktop_sc_path):
                print("* removing {}...".format(desktop_sc_path))
                os.remove(desktop_sc_path)
    else:
        msg = "unknown shortcut format " + sc_ext
        push_label("{} shortcut failed since".format(action))
        push_label(msg)
        print(msg)
    return ret
