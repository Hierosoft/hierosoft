# -*- coding: utf-8 -*-
from __future__ import print_function
import copy
import hashlib
import os
import platform
import shutil
import stat
import sys
import subprocess
import tarfile
import tempfile
from typing import Callable
import zipfile

from zipfile import ZipFile

from hierosoft.morelogging import hr_repr

from hierosoft import (
    echo0,
    write0,
    get_subdir_names,
    sysdirs,
)

from hierosoft.morebytes import (
    rewrite_conf,
    rewrite_conf_str,
)


enable_gi = False

DEFAULT_SIZE_SUB = "48x48"
DEFAULT_CONTEXT = "apps"

APP_ICONS_PATHS = [  # which_pixmap checks others beyond DEFAULT_CONTEXT
    os.path.join("/usr/share/icons/hicolor", DEFAULT_SIZE_SUB,
                 DEFAULT_CONTEXT),
    os.path.join("/usr/local/share/icons/hicolor", DEFAULT_SIZE_SUB,
                 DEFAULT_CONTEXT),
    os.path.join(sysdirs['LOCALAPPDATA'], "icons"),
    os.path.join(sysdirs['LOCALAPPDATA'], "icons", "hicolor", DEFAULT_SIZE_SUB,
                 DEFAULT_CONTEXT),
    # NOTE: ^ hierosoft LOCALAPPDATA is ~/.local/share like .NET framework
    sysdirs['PIXMAPS'],
    os.path.join("/usr/share/icons/hicolor/scalable", DEFAULT_CONTEXT),
    os.path.join("/usr/local/share/icons/hicolor/scalable", DEFAULT_CONTEXT),
]

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    FileExistsError = IOError
    ModuleNotFoundError = ImportError

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    enable_gi = True
except ModuleNotFoundError:
    print("gi is not installed. Icon checks will use {}"
          .format(APP_ICONS_PATHS))
    pass


# TODO: if shlex is used, do (or contribute code to six?):
"""
if sys.version_info.major > 3 and sys.version_info.minor > 8:
    shlex_join = shlex.join
else:
    import pipes  # deprecated, slated for removal in 3.13
    def shlex_join(parts):
        return ' '.join(pipes.quote(arg) for arg in split_command)
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

ICON_THEME = None


def startfile(cell_content):
    if os.name == "nt":  # Windows
        os.startfile(cell_content)
    elif sys.platform == "darwin":  # macOS
        subprocess.call(["open", cell_content])
    else:  # Linux and others
        subprocess.call(["xdg-open", cell_content])


def open_folder_select_file(path):
    if platform.system() == "Windows":
        cmd_parts = ["explorer", "/select,", path.replace("/", "\\")]
        # ^ Yes, it is "/select," (with comma)...because Windows.
        print("open_folder_select_file: " + " ".join(cmd_parts))
        subprocess.Popen(cmd_parts)
    # TODO: elif platform.system() == "Darwin":
    else:
        parent = os.path.dirname(path)
        cmd_parts = ["xdg-open", parent]
        subprocess.Popen(cmd_parts)


def which_pixmap(name, context=DEFAULT_CONTEXT, size=48, refresh=True):
    """Find an icon file in XDG-like locations.

    If moreplatform.enable_gi is True (starts as True if can be
    imported), Gtk will be used to get the icon path. Gtk can get the
    specific icon of the specific theme, but you should set
    "Icon={name}" if found, since an XDG-compatible DE can find the icon
    automatically and use the theme's when the theme changes.

    Args:
        name (str): Icon name (A well-known application name or
            any application with an icon installed).
        context (str, optional): The icon category to check, as in the
            subfolder under /usr/share/icons/hicolor/48x48/ and similar
            XDG-like paths in APP_ICONS_PATHS that end with an "apps"
            (which is the DEFAULT_CONTEXT). Defaults to DEFAULT_CONTEXT.
        refresh (bool, optional): Reload the theme. Ignored if not
            moreplatform.enable_gi.

    Returns:
        str: Path to the icon or None
    """
    global ICON_THEME
    # a.k.a. icon_exists, icon_path, or which_icon_image.
    #   This is the image! For the desktop file, see which_icon
    #   in whichicon.py in linuxpreinstall
    #   (<https://github.com/Hierosoft/linux-preinstall>).
    if enable_gi:
        if not refresh:
            if not ICON_THEME:
                refresh = True
        if refresh:
            icon_theme = Gtk.IconTheme.get_default()
            ICON_THEME = icon_theme
        else:
            icon_theme = ICON_THEME
        # return icon_theme.has_icon(name)
        icon_info = icon_theme.lookup_icon(name, size, 0)
        if icon_info:
            # gi gets the one actually used such as
            #   os.path.join(HOME, "/.local/share/icons/ePapirus-Dark/"
            #                      "48x48/categories/gimp.svg")
            return icon_info.get_filename()

    size_sub = "{}x{}".format(size, size)
    for raw_parent in APP_ICONS_PATHS:
        parent = raw_parent
        grandparent, constant_context = os.path.split(parent)
        ggparent, constant_size_sub = os.path.split(grandparent)
        # ^ ggparent is great-grandparent such as /usr/share/icons/hicolor
        if ((constant_size_sub == DEFAULT_SIZE_SUB)
                and (size_sub != DEFAULT_SIZE_SUB)):
            grandparent = os.path.join(ggparent, size_sub)
            parent = os.path.join(grandparent, constant_context)
            # ^ must set parent here too in case using DEFAULT_CONTEXT
        if constant_context == DEFAULT_CONTEXT:
            if context != DEFAULT_CONTEXT:
                parent = os.path.join(grandparent, context)
        dot_exts = [".png", ".svg", ".xpm"]
        # "supported image file formats are PNG, XPM and SVG"
        # -<https://specifications.freedesktop.org/icon-theme-spec/latest/>
        # 2024-08-20
        try_no_ext_path = os.path.join(parent, name)
        for dot_ext in dot_exts:
            try_path = try_no_ext_path + dot_ext
            if os.path.isfile(try_path):
                return try_path
    return None


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
              % hr_repr(programs_dir))
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
                                % hr_repr(dst))
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


def install_extracted(extracted_path, dst, event_template=None):
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
    names = get_subdir_names(extracted_path) or []  # Do *not* use os.listdir:
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
        evt['error'] = "The file doesn't exist: %s" % hr_repr(archive)
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            extracted_path = os.path.join(tmpdirname, "extracted")
            with tarfile.open(archive, mode) as archive_handle:
                # for i in archive_handle:
                #     archive_handle.extractfile(i)
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
        evt['error'] = "The file doesn't exist: %s" % hr_repr(archive)
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
        echo0("Error extracting %s: %s" % (hr_repr(archive), ex))
        delete_msg = "Deleting %s" % hr_repr(archive)
        evt['error'] += "\n" + delete_msg
        echo0(delete_msg)
        try:
            os.remove(archive)
        except PermissionError:
            permission_msg = ("Cannot delete %s."
                              " Delete the faulty file manually."
                              % archive)
            echo0(permission_msg)
            evt['error'] + "\n" + permission_msg
    return evt


def install_archive(archive, dst, remove_dst=False,
                    remove_archive=True, event_template=None,
                    status_cb=None):
    # type: (str, str, bool, bool, dict, Callable) -> dict[str,str]
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
        if status_cb:
            status_cb(evt)
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
        evt['error'] = "Unknown archive extension: %s" % hr_repr(archive)
        installed = evt
    if 'error' not in installed:
        installed['Path'] = dst
    return installed
    # uninstall button & mode removed (too many nested conditions) 20230823
    # TODO: implement uninstall mode & button elsewhere


def make_shortcut(meta, program_name, mgr, push_label=echo0,
                  uninstall=False):
    """Create a shortcut.

    See also install_shortcut.

    Args:
        meta (dict): Data about the program.
        program_name (str): unix-like unique-enough program name.
        mgr (object): A DownloadManager (for callbacks).
        push_label (Callable, optional): Status function accepting a
            string. Defaults to echo0.
        uninstall (bool, optional): Whether to change to uninstall mode
            (remove the shortcut file using the path that this method
            would create). Defaults to False.

    Returns:
        bool: Whether successful.
    """
    installed_path = meta['Path']  # *required*--missing from earlier versions
    ret = True
    desktop_path = mgr.get_desktop_path()
    sc_ext = sysdirs['SHORTCUT_EXT']
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
        CACHE = os.path.join(sysdirs['CACHES'], program_name)
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


def install_shortcut(Exec, dst, project_meta):
    """Install a shortcut to any program on any understood platform.

    See also make_shortcut.

    - sc_template_path is determined based on dst and shortcut_relpath
    - sc_installed_path (path) is determined from OS and shortcut_namespace
      (filename is based on Name on platforms other than Linux).
    - sc_template_path is read, Exec string is filled based on dst
      (the selected destination where the program is installed)
      then the resulting shortcut is saved to sc_installed_path
      (only after temp file is complete).

    Args:
        Exec (string): The executable path where the shortcut
            should point.
        dst (string): The directory path where the program is
            installed.
        project_meta (dict): All metadata describing the program.
            For this method, it must have the keys:
            - 'shortcut' (dict): contains:
              - 'Name': The entire name (except variant) that
                should be displayed as the shortcut's caption.
              - 'GenericName' (Optional[string]): A simplified
                name for the program. If None, the GenericName
                line will be removed from the shortcut. This
                option is only for GNU/Linux systems or other
                systems using XDG.
              - 'Keywords' (Optional[string]): If None, Keywords
                line will be removed from the shortcut. This
                option is only for GNU/Linux systems or other
                systems using XDG.
              - 'Path' (str): The working directory for the
                program. Defaults to dir containing Exec.
            - 'shortcut_relpath': The location of an existing
              shortcut file to use and modify.
            - 'platform_icon_relpath' (dict[string]): A dict
              where the key is platform.system() (Must have
              at least 'Linux', 'Windows', *AND* 'Darwin')
              and the value is the relative path from
              dst to the icon image file.
    Raises:
        FileNotFoundError: If src does not exist.
    """
    if not os.path.isdir(dst):
        raise ValueError("The dst must be an existing directory."
                         " The name will be generated.")
    warning = None
    Name = project_meta['shortcut']['Name']
    echo0("Name={}".format(Name))
    platform_icon_relpath = project_meta.get('platform_icon_relpath')
    icon_relpath = None
    if platform_icon_relpath is not None:
        icon_relpath = platform_icon_relpath.get(platform.system())
    if icon_relpath is None:
        raise NotImplementedError(
            "There is no platform icon for {}.".format(platform.system())
        )
    Icon = os.path.join(dst, icon_relpath)
    shortcut_meta = copy.deepcopy(project_meta.get('shortcut'))
    shortcut_meta['Name'] = Name
    shortcut_meta['Exec'] = Exec
    shortcut_meta['Icon'] = Icon
    if not project_meta['shortcut'].get('Path'):
        shortcut_meta['Path'] = os.path.dirname(Exec)

    # ^ rewrite_conf_str *removes* any lines where value is None

    if platform.system() == "Linux":
        sc_template_path = os.path.join(dst, project_meta['shortcut_relpath'])
        shortcut_name = "{}.desktop".format(
            project_meta['shortcut_namespace'],  # must include -variant if any
        )
        sc_installed_path = os.path.join(
            sysdirs['SHORTCUTS_DIR'],
            shortcut_name
        )
        if not os.path.isdir(sysdirs['SHORTCUTS_DIR']):
            os.makedirs(sysdirs['SHORTCUTS_DIR'])  # default mode is 511
        write0('Installing icon to "{}"...'.format(sc_installed_path))
        rewrite_conf_str(
            sc_template_path,
            sc_installed_path,
            changes=shortcut_meta,
        )
        echo0("OK")
    elif platform.system() == "Darwin":
        shortcut_name = Name + ".command"
        sc_installed_path = os.path.join(
            sysdirs['SHORTCUTS_DIR'],
            shortcut_name
        )
        with open(sc_installed_path) as stream:
            stream.write('"%s"\n' % Exec)
            # ^ Run the game & close Command Prompt immediately.
            # ^ First arg is Command Prompt title, so leave it blank.
        st = os.stat(sc_installed_path)
        os.chmod(sc_installed_path, st.st_mode | stat.S_IXUSR)
        # ^ same as stat.S_IEXEC: "Unix V7 synonym for S_IXUSR."
    elif platform.system() == "Windows":
        shortcut_name = Name + ".bat"
        sc_installed_path = os.path.join(
            sysdirs['SHORTCUTS_DIR'],
            shortcut_name
        )
        with open(sc_installed_path) as stream:
            stream.write('start "" "%s"\n' % Exec)
            # ^ Run the game & close Command Prompt immediately.
            # ^ First arg is Command Prompt title, so leave it blank.
    else:
        warning = ("Icon install isn't implemented for {}."
                   "".format(platform.system()))
    return {
        'sc_path': sc_installed_path,
        'shortcut_meta': shortcut_meta,
        "warning": warning,  # may be None
        "destination": dst,
    }


def get_dir_size(path, add_symlinks=False):
    total_size = os.path.getsize(path)
    for sub in os.listdir(path):
        sub_path = os.path.join(path, sub)
        if os.path.islink(sub_path) and not add_symlinks:
            continue
        if os.path.isfile(sub_path):
            total_size += os.path.getsize(sub_path)
        elif os.path.isdir(sub_path):
            total_size += get_dir_size(sub_path)
    return total_size


def _zip_dir(zipfile, src, dst, simulate=False):
    if os.path.isfile(src):
        if not simulate:
            zipfile.write(src, dst)
        return 1
    count = 0
    for sub in os.listdir(src):
        # is already known to be a dir
        src_sub_path = os.path.join(src, sub)
        dst_sub_path = os.path.join(dst, sub)
        count += zip_dir(zipfile, src_sub_path, dst_sub_path)
    return count


def zip_dir(zipfile, src, dst, simulate=False):
    if dst.startswith(os.path.sep) or dst.startswith("/"):
        raise ValueError('dst may not start with slash: "{}"'
                         ''.format(dst))
    if platform.system() == "Windows":
        if ":" in dst:
            raise ValueError('dst may not contain ":": "{}"'
                             ''.format(dst))
    return _zip_dir(zipfile, src, dst)


def get_digest(path):
    """Get MD5 digest bytes.

    Args:
        path (str): Any file.

    Returns:
        bytes: md5 digest bytes
    """
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
        return hasher.digest()


def get_hexdigest(path):
    """Get MD5 digest hex-encoded string.

    Args:
        path (str): Any file.

    Returns:
        str: md5 digest hex string.
    """
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
        return hasher.hexdigest()


def same_hash(path1, path2):
    # Based on https://stackoverflow.com/a/36873550/4541104 by unutbu
    digests = []
    for path in (path1, path2):
        hasher = hashlib.md5()
        with open(path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
            a = hasher.hexdigest()
            digests.append(a)

    return digests[0] == digests[1]
