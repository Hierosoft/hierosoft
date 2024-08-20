# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import subprocess
import platform

from datetime import datetime

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    ModuleNotFoundError = ImportError
    NotADirectoryError = OSError
    # ^ such as:
    #   "NotADirectoryError: [Errno 20] Not a directory: '...'" where
    #   "..." is a file and the call is os.listdir.

# The polyfills below are used in other file(s) in the module.

if sys.version_info.major >= 3:
    # from subprocess import run as sp_run

    # Globals used:
    # import subprocess
    from subprocess import CompletedProcess
    from subprocess import run as sp_run
else:
    class CompletedProcess:
        '''
        This is a Python 2 substitute for the Python 3 class.
        '''
        _custom_impl = True

        def __init__(self, args, returncode, stdout=None, stderr=None):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

        def check_returncode(self):
            if self.returncode != 0:
                err = subprocess.CalledProcessError(self.returncode,
                                                    self.args,
                                                    output=self.stdout)
                raise err
            return self.returncode

    def sp_run(*popenargs, **kwargs):
        '''subprocess.run substitute for Python 2
        CC BY-SA 4.0
        by Martijn Pieters
        https://stackoverflow.com/a/40590445
        and Poikilos
        '''
        this_input = kwargs.pop("input", None)
        check = kwargs.pop("handle", False)

        if this_input is not None:
            if 'stdin' in kwargs:
                raise ValueError('stdin and input arguments may not '
                                 'both be used.')
            kwargs['stdin'] = subprocess.PIPE

        process = subprocess.Popen(*popenargs, **kwargs)
        try:
            outs, errs = process.communicate(this_input)
        except Exception as ex:
            process.kill()
            process.wait()
            raise ex
        returncode = process.poll()
        # print("check: {}".format(check))
        # print("returncode: {}".format(returncode))
        if check and returncode:
            raise subprocess.CalledProcessError(returncode, popenargs,
                                                output=outs)
        return CompletedProcess(popenargs, returncode, stdout=outs,
                                stderr=errs)
    subprocess.run = sp_run

from hierosoft.morelogging import (  # noqa F401
    echo0,
    echo1,
    echo2,
    echo3,
    echo4,
    write0,
    write1,
    write2,
    write3,
    write4,
    set_verbosity,
    get_verbosity,
    # verbosity,
)

from hierosoft.sysdirs import sysdirs

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(MODULE_DIR, "assets")
assets_dirs = [ASSETS_DIR]

__version__ = "0.1.0"


def resource_add_path(path):
    """Add a new directory for resource_find.

    Mimic Kivy's behavior.

    Args:
        path (string): The directory to try (successful
            runs of resource_find will try this path).
    """
    assets_dirs.append(path)


def resource_find(filename, use_cache=False):
    """Find a file in known asset directories.

    Mimic Kivy's behavior.

    To add a new asset directory, call resource_add_path
    first.

    Args:
        path (string): The file or path to find.
        use_cache (boolean): Reserved for future use
            (present to mimic Kivy's behavior).

    Returns:
        The full path, or None if not found.
    """
    for asset_dir in assets_dirs:
        try_path = os.path.join(asset_dir, filename)
        if os.path.exists(try_path):
            return try_path
    return None


def get_missing_paths(destination, good_flag_files):
    """
    Args:
        good_flag_files (Iterable[str]): All of these relative
            paths must exist in the destination.

    Returns:
        list (str): Missing paths (full paths)
    """
    missing_paths = []
    for flag_name in good_flag_files:
        flag_path = os.path.join(destination, flag_name)
        if not os.path.isfile(flag_path):
            missing_paths.append(flag_path)
    return missing_paths


def app_version_dir(org_name, app_name, version):
    """Get a path for installing an app into Hierosoft launcher.

    For uninstall data use LOCALAPPDATA (such as ~/.local/share on
    linux) instead of PROGRAMS (such as ~/.local/lib on linux)!

    Args:
        org_name (str): The name of the organization, with no spaces.
            Example: minetest.io
        app_name (str): The unique-enough id of the app, with no
            spaces. Examples: "minetest", "finetest" (or if compiled,
            "finetest-local")
        version (str): The unique version of the app, with no spaces.
            Examples: "0.4", "0.4-dev", "current".
            - If multi-version support is not selected by user, use
              version="current" to upgrade continuously. HInstall tries
              to create rollback data (Uses hierosoft.appstates_dir).
    """
    # formerly get_happ_path
    happs = os.path.join(sysdirs['PROGRAMS'], "hierosoft", "apps")
    # ^ such as in ~/.local/lib on linux
    return os.path.join(happs, org_name, app_name, version)


def appstates_dir(org_name, app_name, version):
    """Get a path for installing an app into Hierosoft launcher.

    For uninstall data use LOCALAPPDATA (such as ~/.local/share on
    linux) instead of PROGRAMS (such as ~/.local/lib on linux)!

    Args:
        org_name (str): The name of the organization, with no spaces.
            Example: minetest.io
        app_name (str): The unique-enough id of the app, with no
            spaces. Examples: "minetest", "finetest" (or if compiled,
            "finetest-local").
        version (str): The unique version of the app, with no spaces.
            Examples: "0.4", "0.4-dev", "current".
            - If multi-version support is not selected by user, use
              version="current" to upgrade continuously. HInstall tries
              to create rollback data. In this case, this function is
              the rollback data parent folder itself.
    """
    appstates = os.path.join(sysdirs['LOCALAPPDATA'], "hierosoft", "appstates")
    # ^ such as in ~/.local/share on linux
    return os.path.join(appstates, org_name, app_name, version)


class TextStream:
    '''Collect streamed strings or bytes
    This class behaves like an opened file in whatever ways are
    appropriate for the hierosoft module such as for the download method
    of hierosoft.moreweb submodule's DownloadManager class.
    '''
    def __init__(self):
        self.data = ""

    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        self.data += data


non_cloud_warning_shown = False

# Note that the enum module is new in Python 3.4, so it isn't used here.
# class SpecialFolder
# See substitutions for ones implemented as a dictionary or ones not from CLR.


def get_unique_path(luid, key, extension=".conf", allow_cloud=False):
    '''Get a unique path for your program within a special folder.
    Purpose: In some cases the extension of the file depends on the
    platform.

    A key that is a plural word (before the colon if present) returns a
    directory and singular return a file.

    Args:
        luid (str): a locally-unique identifier. In other words, this is a name
            that is expected to be unique and not the name of any other
            program installed on the computer in the specified key's
            special folder. The luid shouldn't contain spaces or capital
            letters, but can be a plain text version of the program name,
            such as com.example.MyNameApp on macOS where MyName is the
            program's name and example.com is the domain that is indicated
            in reverse order.

        key (str): Provide a key that is implemented here:
            'Share:Unique': Get your program's path where it may have static
                data.
            'Desktop:Unique': Get your program's platform-specific desktop
                filename. It is your responsibility to create the icon in
                the format designated by the returned file path's extension.
            'Configs:Unique': Get a directory where you can store metadata
                for only your program. You are responsible for creating the
                directory if it doesn't exist. Generally, it is a folder
                within .config (but differs by platform following the
                standards of each platform such as %APPDATA%).
            'Cache:Unique': A directory in the user's cache directory such
                as .cache/{luid}, {LOCALAPPDATA}/cache/{luid} on Windows
                (such as, like on other OSs, not to interfere with the
                install if the program is installed at
                {LOCALAPPDATA}/{luid}).
        allow_cloud (bool, optional): Use the 'Configs:Unique' directory
            in the cloud, but only if a known cloud directory already
            exists (otherwise fall back to 'Configs:Unique' as
            described.
    '''
    global non_cloud_warning_shown
    if key == 'Share:Unique':
        return os.path.join(sysdirs['SHARE'], luid)
    elif key == 'Cache:Unique':
        # if platform.system() == "Windows":
        #     return os.path.join(sysdirs['LOCALAPPDATA'], luid, "cache")
        return os.path.join(sysdirs['CACHES'], luid)
    elif key == 'Desktop:Unique':
        # TODO: Consider using https://github.com/newville/pyshortcuts
        #   to generate shortcut files on Windows/Darwin/Linux.
        if platform.system() == "Windows":
            return os.path.join(sysdirs['SHORTCUTS'], luid+".blnk")
        elif platform.system() == "Darwin":
            return os.path.join(sysdirs['SHORTCUTS'], luid+".desktop")
            # TODO: ^ Use ".command", AppleScript, or something else.
        else:
            return os.path.join(sysdirs['SHORTCUTS'], luid+".desktop")
    elif key == 'Configs:Unique':
        local_unique_dir = os.path.join(sysdirs['APPDATA'], luid)
        if allow_cloud:
            sysdirs.check_cloud()
            if sysdirs['CLOUD_PROFILE'] is not None:
                echo1('* CLOUD_PROFILE="{}"'.format(sysdirs['CLOUD_PROFILE']))
                cloud_unique_dir = os.path.join(sysdirs['CLOUD_PROFILE'],
                                                luid)
                if os.path.isdir(local_unique_dir):
                    if not non_cloud_warning_shown:
                        echo0('Warning: You can merge (then delete) the old'
                              ' "{}" with the new "{}".'
                              ''.format(local_unique_dir, cloud_unique_dir))
                        non_cloud_warning_shown = True
                return cloud_unique_dir
        echo1('* APPDATA="{}"'.format(sysdirs['APPDATA']))
        echo1('* localUniqueDir="{}"'.format(local_unique_dir))
        return local_unique_dir
    else:
        raise KeyError(
            "[hierosoft] The key '{}' is not valid for get_unique_path."
            "".format(key)
        )


def join_if_exists(parent, sub):
    """Join an existing sub(s), otherwise return none.

    Args:
        parent (str): The parent directory possibly containing sub(s).
            If it is not a string, it is assumed to be an iterable and
            each element will be tried as a path string that may
            contain sub.
        sub (str): A path or multiple paths (assumed to be iterable if
            not str).
    """
    if isinstance(parent, str):
        parents = [parent]
    else:
        parents = parent

    if isinstance(sub, str):
        subs = [sub]
    else:
        subs = sub
    for parent in parents:
        for sub in subs:
            try_path = os.path.join(parent, sub)
            if os.path.exists(try_path):
                return try_path
    return None


def replace_isolated(path, old, new, case_sensitive=True):
    '''Replace old only if it is at the start or end of a path
    or is enclosed by a os.path.sep character on each end.
    '''
    if case_sensitive:
        if path.startswith(old):
            path = new + path[len(old):]
        elif path.endswith(old):
            path = path[:-len(old)] + new
        else:
            enclosed_new = os.path.sep + new + os.path.sep
            enclosed_old = os.path.sep + old + os.path.sep
            path = path.replace(enclosed_old, enclosed_new)
    else:
        if path.lower().startswith(old.lower()):
            path = new + path[len(old):]
        elif path.lower().endswith(old.lower()):
            path = path[:-len(old)] + new
        else:
            enclosed_new = os.path.sep + new + os.path.sep
            enclosed_old = os.path.sep + old + os.path.sep
            at = 0
            while at >= 0:
                at = path.lower().find(old.lower())
                if at < 0:
                    break
                rest_i = at + len(old)
                path = path[:at] + new + path[rest_i:]
    return path


def replace_vars(path):
    '''
    Returns:
    The string with variables like $CLOUD or %CLOUD% or %USERPROFILE%
    replaced regardless of the operating system, or None if that is the
    entire path and the value is blank (not detected by sysdirs
    initialization by any means).
    '''
    for old, new in sysdirs.substitutions().items():
        if new is None:
            # Ignore it. It is ok to be None, such as if no
            #   value for $CLOUD (or %CLOUD%) was found.
            continue
            # raise ValueError("{} is None.".format(old))
            if path == old:
                # Return "" if the whole thing is blank.
                return None
        if old.startswith("%") and old.endswith("%"):
            path = path.replace(old, new)
        else:
            path = replace_isolated(path, old, new)
    return path


trues = ["on", "true", "yes", "1"]


def is_truthy(v):
    if v is None:
        return False
    elif v is True:
        return True
    elif v is False:
        return False
    elif isinstance(v, str):
        if v.lower() in trues:
            return True
    elif isinstance(v, int):
        if v != 0:
            return True
    elif isinstance(v, float):
        if v != 0:
            return True
    return False


def s2or3(s):
    '''
    Make sure the string is compatible with the Python version.
    '''
    if sys.version_info.major < 3:
        if type(s).__name__ == "unicode":
            # ^ such as a string returned by json.load*
            #   using Python 2
            return str(s)
    if type(s).__name__ == "bytes":
        return s.decode()
    return s


def no_enclosures(
        s,
        openers=["(", "[", "{", '"', "'"],
        closers=[")", "]", "}", '"', "'"],
):
    """Remove the enclosures from a string.

    For example, change "(12-22-2022)" to "12-22-2022".

    Args:
        openers (Optional[list[str]]): The delimiters that start the
            scope such as "(" or '"'.
        closers (Optional[list[str]]): The delimiters that end the scope
            such as ")" or '"'. Each item must be paired with the same
            index in openers.

    Returns:
        str: The original string without enclosures.
    """
    if len(openers) != len(closers):
        raise ValueError(
            "The openers and closers must be paired in order"
            " but len(openers)={} and len(closers)={}"
            "".format(len(openers), len(closers))
        )
    if len(s) < 2:
        return s
    for i in range(len(openers)):
        if s.startswith(openers[i]) and s.endswith(closers[i]):
            return s[1:-1]
    return s


def find_by_value(items, key, value):
    '''
    Find an index in a list of dicts using the key and value.
    '''
    for i in range(len(items)):
        if items[i].get(key) == value:
            return i
    return -1


def number_to_place(num):
    '''
    Convert a number such as 1 to a string such as 1st.
    '''
    num_s = str(num)
    if num_s.endswith("1") and (num != 11):
        return num_s + "st"
    elif num_s.endswith("2") and (num != 12):
        return num_s + "nd"
    elif num_s.endswith("3") and (num != 13):
        return num_s + "rd"
    return num_s + "th"


def run_and_get_lists(cmd_parts, collect_stderr=True):
    '''Run a command and check the output.

    Args:
        collect_stderr (bool): Collect stderr output for the err return
            list Defaults to True.

    Returns:
        tuple[list[str], list[str], int]: (out, err, returncode) where
            out and err are each a list of 0 or more lines, and return
            code is the code returned by the process (0 if ok).
    '''
    # See <https://stackabuse.com/executing-shell-commands-with-python>:
    # called = subprocess.run(list_installed_parts,
    #                         stdout=subprocess.PIPE, text=True)
    # , input="Hello from the other side"
    # echo0(called.stdout)
    outs = []
    errs = []
    # See <https://stackoverflow.com/a/7468726/4541104>
    # "This approach is preferable to the accepted answer as it allows
    # one to read through the output as the sub process produces it."
    # -Hoons Jul 21 '16 at 23:19
    if collect_stderr:
        sp = subprocess.Popen(cmd_parts, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    else:
        sp = subprocess.Popen(cmd_parts, stdout=subprocess.PIPE)

    if sp.stdout is not None:
        for raw_ in sp.stdout:
            line = raw_.decode()
            # TODO: is .decode('UTF-8') ever necessary?
            outs.append(line.rstrip("\n\r"))
    if sp.stderr is not None:
        for raw_ in sp.stderr:
            line = raw_.decode()
            while True:
                back_i = line.find("\b")
                if back_i < 0:
                    break
                elif back_i == 0:
                    print("WARNING: Removing a backspace from the"
                          " start of \"{}\".".format(line))
                line = line[:back_i-1] + line[back_i+1:]
                # -1 to execute the backspace not just remove it
            errs.append(line.rstrip("\n\r"))
    # MUST finish to get returncode
    # (See <https://stackoverflow.com/a/16770371>):
    more_out, more_err = sp.communicate()
    if len(more_out.strip()) > 0:
        echo0("[run_and_get_lists] got extra stdout: {}".format(more_out))
    if len(more_err.strip()) > 0:
        echo0("[run_and_get_lists] got extra stderr: {}".format(more_err))

    # See <https://stackoverflow.com/a/7468725/4541104>:
    # out, err = subprocess.Popen(
    #     ['ls','-l'],
    #     stdout=subprocess.PIPE,
    # ).communicate()

    # out, err = sp.communicate()
    # (See <https://stackoverflow.com/questions/10683184/
    # piping-popen-stderr-and-stdout/10683323>)
    # if out is not None:
    #     for raw_ in out.splitlines():
    #         line = raw_.decode()
    #         outs.append(line.rstrip("\n\r"))
    # if err is not None:
    #     for raw_ in err.splitlines():
    #         line = raw_.decode()
    #         errs.append(line.rstrip("\n\r"))

    return outs, errs, sp.returncode


def get_subdir_names(folder_path, hidden=False):
    ret = []
    if os.path.exists(folder_path):
        ret = []
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if ((hidden or sub_name[:1] != ".") and os.path.isdir(sub_path)):
                ret.append(sub_name)
    return ret


def get_file_names(folder_path, hidden=False):
    ret = None
    if os.path.exists(folder_path):
        ret = []
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if ((hidden or sub_name[:1] != ".") and os.path.isfile(sub_path)):
                ret.append(sub_name)
    return ret


def get_ext(filename):
    raise NotImplementedError(
        "get_ext is deprecated."
        " Use os.path.splitext(path)[1] instead."
    )
    ext = ""
    dot_i = filename.rfind('.')
    if dot_i > -1:
        ext = filename[dot_i+1:]
    return ext


# program_name is same as dest_id
def get_installed_bin(programs_path, dest_id, flag_names):
    """Get an installed binary name.

    Args:
        programs_path (string): The folder containing programs
            (or contains versions of the program for a multi-version
            folder structure).

    Returns:
        string: The full path to the installed program, or None
            if not installed.
    """
    if flag_names is None:
        raise ValueError(
            "You must specify known filename(s) where 1 or more"
            " would exist in programs_path/dest_id/ if dest_id is installed"
        )
    for flag_name in flag_names:
        installed_path = os.path.join(programs_path, dest_id)
        flag_path = os.path.join(installed_path, flag_name)
        if os.path.isfile(flag_path):
            return
    return None


def is_installed(programs_path, dest_id, flag_names):
    path = get_installed_bin(programs_path, dest_id, flag_names)
    return (path is not None)


def is_exe(path):
    """Check if the path exists and is executable.

    Returns:
        bool: Is an executable file.
    """
    # Jay, & Mar77i. (2017, November 10). Path-Test if executable exists in
    #     Python? [Answer]. Stack Overflow.
    #     https://stackoverflow.com/questions/377017/
    #     test-if-executable-exists-in-python
    return os.path.isfile(path) and os.access(path, os.X_OK)


WIN_EXECUTABLE_DOT_EXTS = [".exe", ".ps1", ".bat", ".com"]


def which(program_name, more_paths=[]):
    '''Get the full path to a given executable.
    This avoids shutil.which which requires Python 3.3 (not backported to 2)

    If a full path is provided,
    return it if executable. Otherwise, if there isn't an executable one
    the PATH, return None, or return one that exists but isn't
    executable (using program_name as the preferred path if it is a full
    path even if not executable).

    Args:
        program_name (str): This can leave off the potential file extensions
            and on Windows each known file extension will be checked (for the
            complete list that will be checked, see the
            WIN_EXECUTABLE_DOT_EXTS constant in the module's
            __init__.py.
        more_paths (Iterable[str]): Paths other than those in system PATH
            that should also be checked.

    Returns:
        str: The full path to the executable or None.
    '''
    prefix = "[which] "
    # from https://github.com/poikilos/DigitalMusicMC
    preferred_path = None
    filenames = [program_name]
    if platform.system() == "Windows":
        if program_name == "libreoffice":
            filenames.insert(0, "soffice")  # This is correct on Windows
        new_filenames = []
        for old_filename in filenames:
            new_filenames.append(old_filename)
            if os.path.splitext(program_name)[1] == "":  # if no ext
                for dot_ext in WIN_EXECUTABLE_DOT_EXTS:
                    new_filenames.append(old_filename+dot_ext)
        filenames = new_filenames
        if more_paths is None:
            more_paths = []

        title = program_name.title()
        # If it is LibreOffice, the folder name is still LibreOffice
        #   (so only use program_name here):
        more_paths.append("C:\\Program Files\\{}".format(title))
        more_paths.append("C:\\Program Files\\{}\\bin".format(title))
        more_paths.append("C:\\Program Files\\{}\\program".format(title))
        more_paths.append("C:\\Program Files (x86)\\{}".format(title))
        more_paths.append("C:\\Program Files (x86)\\{}\\bin".format(title))
        more_paths.append("C:\\Program Files (x86)\\{}\\program".format(title))
        # It's "C:\Program Files\LibreOffice\program\soffice.exe" in v24.2.1.2
    for filename in filenames:
        if os.path.split(filename)[0] and is_exe(filename):
            return filename
        elif os.path.isfile(filename):
            preferred_path = filename

        paths_str = os.environ.get('PATH')
        if paths_str is None:
            echo2("Warning: There is no PATH variable, so returning {}"
                  "".format(filename))
            return filename

        paths = paths_str.split(os.path.pathsep)
        fallback_path = None
        for path in (paths + more_paths):
            echo3(prefix+"looking in {}".format(path))
            try_path = os.path.join(path, filename)
            if is_exe(try_path):
                return try_path
            elif os.path.isfile(try_path):
                echo2(prefix+'Warning: "{}" exists'
                      ' but is not executable.'.format(try_path))
                fallback_path = try_path
            else:
                echo3(prefix+"There is no {}".format(try_path))
        result = None
        if preferred_path is not None:
            echo2(prefix+'Warning: "{}" will be returned'
                  ' since given as filename="{}" but is not executable.'
                  ''.format(preferred_path, filename))
            result = fallback_path
        elif fallback_path is not None:
            echo2(prefix+'Warning: "{}" will be returned'
                  ' but is not executable.'.format(fallback_path))
            result = fallback_path
    return result


def which_python():
    more_paths = []
    names = ["python3", "python"]
    if platform.system() == "Windows":
        names = ["pythonw", "python"]
    for name in names:
        got = which(name, more_paths=more_paths)
        if got:
            return got
    return None


def get_pyval(name, py_path):
    line_n = 0
    with open(py_path, 'r') as f:
        for raw_ in f:
            line_n += 1  # counting starts at 1
            line = raw_.strip()
            parts = line.split("=")
            for i in range(len(parts)):
                parts[i] = parts[i].strip()
            if len(parts) < 2:
                continue
            if parts[0] == name:
                quoted_value = parts[1]
                quote = quoted_value[0]
                ender_i = quoted_value.find(quote, 1)
                while ((ender_i > -1) and (quoted_value[ender_i-1] == "\\")):
                    # If preceded by escape char, look further ahead.
                    ender_i = quoted_value.find(quote, ender_i)
                if ender_i < 0:
                    echo0('{}:{}: SyntaxError: There was no ending {}'
                          ''.format(py_path, line_n, quote))
                    continue
                return quoted_value[1:ender_i]


def generate_caption(project_meta, variant):
    """Generate the icon caption.

    Args:
        project_meta (dict): The dict containing 'name' and
            'name_and_variant_fmt' where 'name' is like
            "Finetest (minetest.org)", and 'name_and_variant_fmt' is
            like 'Minetest ({}) (minetest.org build)'.
            The "{}" will be replaced with the variant.
    """
    name = project_meta['name']
    if variant is not None:
        name_and_variant_fmt = project_meta.get('name_and_variant_fmt')
        if name_and_variant_fmt is not None:
            name = name_and_variant_fmt.format(variant)
        else:
            name += " (" + project_meta['variant'] + ")"  # raise if None
    return name


# Date variables below are borrowed from enissue.py in
# <https://github.com/Poikilos/EnlivenMinetest>, but the sanitized
# version instead of the Gitea-specific version is used:
giteaSanitizedDtFmt = "%Y-%m-%dT%H:%M:%S%z"
sanitizedDtExampleS = "2021-11-25T12:00:13-0500"
# PATH_TIME_FMT = "%Y-%m-%d %H..%M..%S"  # from rotocanvas
# PATH_SUFFIX_FMT = "_%Y-%m-%d_%H_%M_%S"  # from my lepidopterist fork
# "%Y-%m-%d %H..%M..%S" # from rotocanvas
PATH_TIME_FMT = "%Y-%m-%dT%H_%M_%S"


def dt_str(dt):
    """Convert datetime to a string standardized for nopackage metadata.

    Args:
        dt (datetime): Examples: from datetime import timezone;
            datetime.now(timezone.utc); or without tzinfo:
            datetime.utcnow()

    Returns:
        str: Date and time string in giteaSanitizedDtFmt
    """
    # return datetime.strftime(dt, "%Y-%m-%dT%H:%M:%SZ")  # from enissue.py
    return datetime.strftime(dt, giteaSanitizedDtFmt)


def str_dt(timestamp_s):
    return datetime.strptime(timestamp_s, giteaSanitizedDtFmt)


def dt_path_str(dt):
    # a.k.a. datetime_path_str but couldn't find my old method anywhere
    return datetime.strftime(dt, PATH_TIME_FMT)


def path_str_dt(timestamp_s):
    return datetime.strptime(timestamp_s, PATH_TIME_FMT)


if __name__ == "__main__":
    # moreweb is the preloader
    print("You must import this module and call get_meta() to use it"
          "--maybe you meant to run update.pyw", file=sys.stderr)
