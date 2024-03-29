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

    # subprocess.run doesn't exist in Python 2, so create a substitute.
    def sp_run(*popenargs, **kwargs):
        '''
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
    write0,
    write1,
    write2,
    write3,
    set_verbosity,
    get_verbosity,
    # verbosity,
)

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


SHORTCUT_EXT = "desktop"
HOME = None  # formerly profile
APPDATA = None  # formerly APPDATA
LOCALAPPDATA = None  # formerly local
# myLocal = None
SHORTCUTS_DIR = None  # formerly SHORTCUTS_DIR
replacements = None
USER = None  # formerly username
PROFILES = None  # formerly profiles
LOGS = None  # formerly logsDir
CACHES = None
PIXMAPS = None
PREFIX = os.environ.get('PREFIX')
SHARE = None  # formerly share
USER_PROGRAMS = None
# For the rationales behind the values see get_unique_path documentation
if platform.system() == "Windows":
    SHORTCUT_EXT = "bat"
    USER = os.environ.get("USERNAME")
    HOME = os.environ.get("USERPROFILE")
    _data_parent_ = os.path.join(HOME, "AppData")
    APPDATA = os.path.join(_data_parent_, "Roaming")
    LOCALAPPDATA = os.path.join(_data_parent_, "Local")
    USER_PROGRAMS = os.path.join(LOCALAPPDATA, "Programs")
    del _data_parent_
    SHARE = LOCALAPPDATA  # It is synonymous
    SHORTCUTS_DIR = os.path.join(HOME, "Desktop")
    PROFILES = os.environ.get("PROFILESFOLDER")
    temporaryFiles = os.path.join(LOCALAPPDATA, "Temp")
    if PREFIX is None:
        PREFIX = LOCALAPPDATA
    PIXMAPS = PREFIX
    CACHES = os.path.join(LOCALAPPDATA, "cache")
else:
    USER = os.environ.get("USER")
    HOME = os.environ.get("HOME")
    LOCALAPPDATA = os.path.join(HOME, ".local", "share")
    # ^ "home/.local/share" -<developers.redhat.com/blog/2018/11/07
    #   /dotnet-special-folder-api-linux>
    # ^ Or os.path.join(HOME, ".var") maybe??
    USER_PROGRAMS = os.path.join(HOME, ".local", "lib")
    # ^ Or os.path.join(HOME, ".local", "share") maybe??
    SHARE = LOCALAPPDATA  # synonymous; generally written on install
    if platform.system() == "Darwin":
        SHORTCUT_EXT = "command"
        # See also <https://github.com/poikilos/world_clock>

        SHORTCUTS_DIR = os.path.join(HOME, "Desktop")
        Library = os.path.join(HOME, "Library")
        APPDATA = os.path.join(Library, "Application Support")
        USER_PROGRAMS = os.path.join(APPDATA, "Programs")  # FIXME nonstandard
        # LOCALAPPDATA = APPDATA
        '''
        ^ According to <https://forum.unity.com/threads/
          solved-special-folder-path-in-mac.23686/#post-157339>.
          There are also the following:
          ~/Library/Preferences/<[appname]>/ [edit using NSUserDefaults]
          ~/Library/<application name>/
          and those and Application Support without ~ making 3 in the
          root directory according to
          <https://apple.stackexchange.com/a/28930> and according to
          McLawrence' comment if the app is from the app store it will
          be in ~/Library/Containers/<application name>/
          According to the File System Programming guide cited above,
          <https://developer.apple.com/library/archive/documentation/
          FileManagement/Conceptual/FileSystemProgrammingGuide/
          MacOSXDirectories/MacOSXDirectories.html>, the files
          required for the app to run should be in something like:
          ~/Library/Application Support/com.example.MyApp/
          caches should be in:
          ~/Library/Caches/com.example.MyApp
        '''
        CACHES = os.path.join(Library, "Caches")
        LOGS = os.path.join(HOME, "Library", "Logs")
        # ^ Ensure it is ok to be written manually & unstructured since
        #   <https://developer.apple.com/library/archive/documentation/
        #   FileManagement/Conceptual/FileSystemProgrammingGuide/
        #   MacOSXDirectories/MacOSXDirectories.html> says,
        #   ". . . Users can also view these logs using the
        #   Console app."
        PROFILES = "/Users"
        temporaryFiles = os.environ.get("TMPDIR")
        if PREFIX is None:
            PREFIX = Library   # TODO: Consider whether this is best.
        SHARE = LOCALAPPDATA  # synonymous
    else:
        if PREFIX is None:
            PREFIX = os.path.join(HOME, ".local")
        # GNU+Linux Systems
        SHARE = os.path.join(PREFIX, "share")
        SHORTCUTS_DIR = os.path.join(SHARE, "applications")
        _default_localappdata = LOCALAPPDATA
        # region based on <developers.redhat.com/blog/2018/11/07
        #   /dotnet-special-folder-api-linux>
        LOCALAPPDATA = os.environ.get('XDG_DATA_HOME')
        if not LOCALAPPDATA:
            LOCALAPPDATA = _default_localappdata  # ~/.local/share
        APPDATA = os.environ.get('XDG_CONFIG_HOME')
        if not APPDATA:
            APPDATA = os.path.join(HOME, ".config")
        CommonApplicationData = "/usr/share"
        CommonTemplates = "/usr/share/templates"

        # endregion based on <developers.redhat.com/blog/2018/11/07
        #   /dotnet-special-folder-api-linux>
        # LOCALAPPDATA = APPDATA
        LOGS = os.path.join(HOME, ".var", "log")
        PROFILES = "/home"
        temporaryFiles = "/tmp"


PIXMAPS = os.path.join(SHARE, "pixmaps")


localBinPath = os.path.join(PREFIX, "bin")

if CACHES is None:
    CACHES = os.path.join(HOME, ".cache")

# TODO: Consider using os.path.expanduser('~') to get HOME.
if HOME != os.path.expanduser('~'):
    echo0("[moreplatform] Warning:")
    echo0('  HOME="{}"'.format(HOME))
    echo0('  != os.path.expanduser("~")="{}"'.format(os.path.expanduser('~')))


USER_DIR_NAME = os.path.split(HOME)[1]
# ^ may differ from os.getlogin() getpass.getuser()
try:
    # doesn't matter. USER will be used (from env) anyway.
    if hasattr(os, "getlogin"):
        if USER_DIR_NAME != os.getlogin():
            echo1("Verbose warning:")
            echo1('  USER_DIR_NAME="{}"'.format(USER_DIR_NAME))
            echo1('  != os.getlogin()="{}"'.format(os.getlogin()))
    else:
        pass
        # echo0("There is no os.getlogin (normally not present for Python 2),"
        #       " so USER_DIR_NAME not validated: %s. Using instead."
        #       % USER_DIR_NAME)
except OSError:
    # os.getlogin() causes:
    # "OSError: [Errno 6] No such device or address"
    # Such as on Python 3.10.6 on Linux Mint 21
    pass

try:
    import getpass  # optional
    if USER_DIR_NAME != getpass.getuser():
        echo1("Verbose warning:")
        echo1('  USER_DIR_NAME="{}"'.format(USER_DIR_NAME))
        echo1('  != getpass.getuser()="{}"'.format(getpass.getuser()))
except ModuleNotFoundError as ex:
    echo1(str(ex))

try:
    import pwd  # optional
    if USER_DIR_NAME != pwd.getpwuid(os.getuid())[0]:
        echo1("Verbose warning:")
        echo1('  USER_DIR_NAME="{}"'.format(USER_DIR_NAME))
        echo1('  != pwd.getpwuid(os.getuid())[0]="{}"'
              ''.format(pwd.getpwuid(os.getuid())[0]))
except ModuleNotFoundError as ex:
    echo1('Skipping optional dependency: {}'.format(ex))


# statedCloud = "owncloud"
myCloudName = None
myCloudPath = None

CLOUD_DIR_NAMES = ["Nextcloud", "ownCloud", "owncloud"]

for tryCloudName in CLOUD_DIR_NAMES:
    # ^ The first one must take precedence if more than one exists!
    tryCloudPath = os.path.join(HOME, tryCloudName)
    if os.path.isdir(tryCloudPath):
        myCloudName = tryCloudName
        myCloudPath = tryCloudPath
        echo1('* detected "{}"'.format(myCloudPath))
        break


# NOTE: PATH isn't necessary to split with os.pathsep (such as ":", not
# os.sep or os.path.sep such as "/") since sys.path is split already.

CLOUD_PROFILE = None  # formerly myCloudProfile; such as ~/Nextcloud/HOME
# myCloudDir = None

# The replacements are mixed since the blnk file may have come from
#   another OS:
substitutions = {
    "%APPDATA%": APPDATA,
    "$HOME": HOME,
    "%LOCALAPPDATA%": LOCALAPPDATA,
    "%MYDOCS%": os.path.join(HOME, "Documents"),
    "%MYDOCUMENTS%": os.path.join(HOME, "Documents"),
    "%PROFILESFOLDER%": PROFILES,
    "%USER%": USER,
    "%USERPROFILE%": HOME,
    "%TEMP%": temporaryFiles,
    "~": HOME,
    "$CLOUD": None,
    "%CLOUD%": None,
}

# ^ For cloud, see check_cloud.
# FIXME: Replace constants above with elements in sysdirs below.


class Constants(dict):
    """Read-only Dictionary.

    based on https://stackoverflow.com/a/19023331/4541104
    """
    def __init__(self):
        dict.__init__(self)
        self.__readonly = False

    def readonly(self, readonly=True):
        """Allow or deny modifying dictionary"""
        if readonly is None:
            readonly = False
        elif readonly not in (True, False):
            raise TypeError("readonly shoul be True or False (got {})"
                            "".format(readonly))
        self.__readonly = readonly

    def __setitem__(self, key, value):
        if self.__readonly:
            raise TypeError("__setitem__ is not supported")
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if self.__readonly:
            raise TypeError("__delitem__ is not supported")
        return dict.__delitem__(self, key)


sysdirs = Constants()  # Call .readonly() after vars are set below.

# For semi-standard folders on Windows and Darwin see
# <johnkoerner.com/csharp/special-folder-values-on-windows-versus-mac/>
if platform.system() == "Windows":
    # HOME = os.environ['USERPROFILE']
    sysdirs['HOME'] = HOME
    sysdirs['SHORTCUTS_DIR'] = os.path.join(HOME, "Desktop")
    sysdirs['APPDATA'] = os.environ['APPDATA']
    sysdirs['LOCALAPPDATA'] = os.environ['LOCALAPPDATA']
    sysdirs['PROGRAMS'] = os.path.join(sysdirs['LOCALAPPDATA'], "Programs")
    sysdirs['CACHES'] = os.path.join(sysdirs['LOCALAPPDATA'], "Caches")
elif platform.system() == "Darwin":
    # See <https://developer.apple.com/library/archive/
    #   documentation/MacOSX/Conceptual/BPFileSystem/Articles/
    #   WhereToPutFiles.html>
    # HOME = os.environ['HOME']
    sysdirs['HOME'] = HOME
    sysdirs['SHORTCUTS_DIR'] = os.path.join(HOME, "Desktop")
    # APPDATA = os.path.join(HOME, "Library", "Preferences")
    # ^ Don't use Preferences: It only stores plist format files
    #   generated using the macOS Preferences API.
    # APPDATA = "/Library/Application Support" # .net-like
    sysdirs['APPDATA'] = os.path.join(HOME, ".config")  # .net Core-like
    sysdirs['LOCALAPPDATA'] = os.path.join(HOME, ".local",
                                           "share")  # .net Core-like
    sysdirs['CACHES'] = os.path.join(HOME, "Library",
                                     "Caches")  # .net Core-like
    # ^ APPDATA & LOCALAPPDATA & CACHES can also be in "/" not HOME
    #   (.net-like)
    # sysdirs['PROGRAMS'] = os.path.join(HOME, "Applications")
    # ^ Should only be used for Application Bundle, so:
    sysdirs['PROGRAMS'] = os.path.join(HOME, ".local", "lib")
else:
    # HOME = os.environ['HOME']
    sysdirs['HOME'] = HOME
    sysdirs['SHORTCUTS_DIR'] = os.path.join(HOME, ".local", "share",
                                            "applications")
    sysdirs['APPDATA'] = os.path.join(HOME, ".config")
    sysdirs['LOCALAPPDATA'] = os.path.join(HOME, ".local",
                                           "share")  # .net-like
    sysdirs['CACHES'] = os.path.join(HOME, ".cache")
    sysdirs['PROGRAMS'] = os.path.join(HOME, ".local", "lib")

# del HOME

sysdirs.readonly()


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
    '''
    Collect streamed strings or bytes. This class behaves like an
    opened file in whatever ways are appropriate for the hierosoft
    module such as for the download method of hierosoft.moreweb
    submodule's DownloadManager class.
    '''
    def __init__(self):
        self.data = ""

    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        self.data += data


def check_cloud(cloud_path=None, cloud_name=None):
    '''
    This will check whether there is a "HOME" directory in your
    cloud path (such as ~/Nextcloud). It will not modify the global
    detected myCloudPath nor myCloudName (if not present, both are None)
    unless you specify a cloud_path.

    Update the substitutions if the cloud exists or is specified,
    whether or not a "HOME" folder exists there.

    Keyword arguments:
    cloud_path -- Set the global myCloudPath. (If None, use the one
        discovered on load, that being any subfolders in Home named
        using any string in the global CLOUD_DIR_NAMES).
    cloud_name -- Set the global cloud name (If None, use the folder
        name of cloud_path if cloud_path was set). This will only be set
        if cloud_path is also set.
    '''
    global CLOUD_PROFILE
    global myCloudPath
    global myCloudName
    if cloud_path is not None:
        myCloudPath = cloud_path
        if cloud_name is not None:
            myCloudName = cloud_name
        else:
            myCloudName = os.path.split(cloud_path)[1]

    if myCloudPath is not None:
        # Update substitutions whether or not the HOME path exists:
        if myCloudPath is not None:
            substitutions['%CLOUD%'] = myCloudPath
            substitutions['$CLOUD'] = myCloudPath
        # Set the HOME path if it exists:
        tryCloudProfileDir = os.path.join(myCloudPath, "profile")
        # ^ Yes, LITERALLY a subdir named "profile",
        #   not profile variable.
        if os.path.isdir(tryCloudProfileDir):
            CLOUD_PROFILE = tryCloudProfileDir
        else:
            print('  * Manually create "{}" to enable cloud saves.'
                  ''.format(tryCloudProfileDir))


check_cloud()


non_cloud_warning_shown = False

# Note that the enum module is new in Python 3.4, so it isn't used here.
# class SpecialFolder
# See substitutions for ones implemented as a dictionary or ones not from CLR.


def get_unique_path(luid, key, extension=".conf", allow_cloud=False):
    '''
    Get a unique path for your program within a special folder. This
    function exists since in some cases, the extension of the file
    depends on the platform.

    A key that is a plural word (before the colon if present) returns a
    directory and singular return a file.

    Sequential arguments:
    luid -- a locally-unique identifier. In other words, this is a name
        that is expected to be unique and not the name of any other
        program installed on the computer in the specified key's
        special folder. The luid shouldn't contain spaces or capital
        letters, but can be a plain text version of the program name,
        such as com.example.MyNameApp on macOS where MyName is the
        program's name and example.com is the domain that is indicated
        in reverse order.

    key -- Provide a key that is implemented here:
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

    Keyword arguments:
    allow_cloud -- Use the 'Configs:Unique' directory in the cloud,
        but only if a known cloud directory already exists (otherwise
        fall back to 'Configs:Unique' as described.
    '''
    global non_cloud_warning_shown
    if key == 'Share:Unique':
        return os.path.join(SHARE, luid)
    elif key == 'Cache:Unique':
        # if platform.system() == "Windows":
        #     return os.path.join(LOCALAPPDATA, luid, "cache")
        return os.path.join(CACHES, luid)
    elif key == 'Desktop:Unique':
        # TODO: Consider using https://github.com/newville/pyshortcuts
        #   to generate shortcut files on Windows/Darwin/Linux.
        if platform.system() == "Windows":
            return os.path.join(SHORTCUTS_DIR, luid+".blnk")
        elif platform.system() == "Darwin":
            return os.path.join(SHORTCUTS_DIR, luid+".desktop")
            # TODO: ^ Use ".command", applescript, or something else.
        else:
            return os.path.join(SHORTCUTS_DIR, luid+".desktop")
    elif key == 'Configs:Unique':
        localUniqueDir = os.path.join(APPDATA, luid)
        if allow_cloud:
            check_cloud()
            if CLOUD_PROFILE is not None:
                echo1('* CLOUD_PROFILE="{}"'.format(CLOUD_PROFILE))
                cloudUniqueDir = os.path.join(CLOUD_PROFILE, luid)
                if os.path.isdir(localUniqueDir):
                    if not non_cloud_warning_shown:
                        echo0('Warning: You can merge (then delete) the old'
                              ' "{}" with the new "{}".'
                              ''.format(localUniqueDir, cloudUniqueDir))
                        non_cloud_warning_shown = True
                return cloudUniqueDir
        echo1('* APPDATA="{}"'.format(APPDATA))
        echo1('* localUniqueDir="{}"'.format(localUniqueDir))
        return localUniqueDir
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
    '''
    Replace old only if it is at the start or end of a path or is
    surrounded by os.path.sep.
    '''
    if case_sensitive:
        if path.startswith(old):
            path = new + path[len(old):]
        elif path.endswith(old):
            path = path[:-len(old)] + new
        else:
            wrappedNew = os.path.sep + new + os.path.sep
            wrappedOld = os.path.sep + old + os.path.sep
            path = path.replace(wrappedOld, wrappedNew)
    else:
        if path.lower().startswith(old.lower()):
            path = new + path[len(old):]
        elif path.lower().endswith(old.lower()):
            path = path[:-len(old)] + new
        else:
            wrappedNew = os.path.sep + new + os.path.sep
            wrappedOld = os.path.sep + old + os.path.sep
            at = 0
            while at >= 0:
                at = path.lower().find(old.lower())
                if at < 0:
                    break
                restI = at + len(old)
                path = path[:at] + new + path[restI:]
    return path


def replace_vars(path):
    '''
    Returns:
    The string with variables like $CLOUD or %CLOUD% or %USERPROFILE%
    replaced regardless of the operating system, or None if that is the
    entire path and the value is blank (not detected by morefolders by
    any means).
    '''
    for old, new in substitutions.items():
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
        for rawL in sp.stdout:
            line = rawL.decode()
            # TODO: is .decode('UTF-8') ever necessary?
            outs.append(line.rstrip("\n\r"))
    if sp.stderr is not None:
        for rawL in sp.stderr:
            line = rawL.decode()
            while True:
                bI = line.find("\b")
                if bI < 0:
                    break
                elif bI == 0:
                    print("WARNING: Removing a backspace from the"
                          " start of \"{}\".".format(line))
                line = line[:bI-1] + line[bI+1:]
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
    #     for rawL in out.splitlines():
    #         line = rawL.decode()
    #         outs.append(line.rstrip("\n\r"))
    # if err is not None:
    #     for rawL in err.splitlines():
    #         line = rawL.decode()
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
        if os.path.splitext(program_name)[1] == "":
            for dot_ext in WIN_EXECUTABLE_DOT_EXTS:
                filenames.append(program_name+dot_ext)
    for filename in filenames:
        if os.path.split(filename)[0] and is_exe(filename):
            return filename
        elif os.path.isfile(filename):
            preferred_path = filename

        paths_str = os.environ.get('PATH')
        if paths_str is None:
            echo0("Warning: There is no PATH variable, so returning {}"
                  "".format(filename))
            return filename

        paths = paths_str.split(os.path.pathsep)
        fallback_path = None
        for path in (paths + more_paths):
            echo1(prefix+"looking in {}".format(path))
            try_path = os.path.join(path, filename)
            if is_exe(try_path):
                return try_path
            elif os.path.isfile(try_path):
                echo0(prefix+'Warning: "{}" exists'
                      ' but is not executable.'.format(try_path))
                fallback_path = try_path
            else:
                echo1(prefix+"There is no {}".format(try_path))
        result = None
        if preferred_path is not None:
            echo0(prefix+'Warning: "{}" will be returned'
                  ' since given as filename="{}" but is not executable.'
                  ''.format(preferred_path, filename))
            result = fallback_path
        elif fallback_path is not None:
            echo0(prefix+'Warning: "{}" will be returned'
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
        for rawL in f:
            line_n += 1  # counting starts at 1
            line = rawL.strip()
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
    Name = project_meta['name']
    if variant is not None:
        name_and_variant_fmt = project_meta.get('name_and_variant_fmt')
        if name_and_variant_fmt is not None:
            Name = name_and_variant_fmt.format(variant)
        else:
            Name += " (" + project_meta['variant'] + ")"  # raise if None
    return Name


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
