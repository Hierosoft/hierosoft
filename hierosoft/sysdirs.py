# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import platform
import sys

from hierosoft.morelogging import (
    echo0,
    echo1,
    echo2,
    echo3,
)
from hierosoft.readonlydict import ReadOnlyOrderedDict

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    ModuleNotFoundError = ImportError
    NotADirectoryError = OSError

class PlatformReadOnlyDict(ReadOnlyOrderedDict):
    def __init__(self):
        ReadOnlyOrderedDict.__init__(self)
        self._substitutions = {
            "$CLOUD": None,
            "%CLOUD%": None,
        }  # ^ CLOUD values are set in check_cloud.

    def substitutions(self):
        self._substitutions.update({
            "%APPDATA%": self['APPDATA'],
            "$HOME": self['HOME'],
            "%LOCALAPPDATA%": self['LOCALAPPDATA'],
            "%MYDOCS%": self['DOCUMENTS'],
            "%MYDOCUMENTS%": self['DOCUMENTS'],
            "%PROFILESFOLDER%": self['PROFILESFOLDER'],
            "%USER%": self['USER'],
            "%USERPROFILE%": self['HOME'],
            "%TEMP%": self['TMP'],
            "~": self['HOME'],
        })  # ^ CLOUD values are set in check_cloud.
        return self._substitutions

    def sanity_check(self):
        # TODO: Consider using os.path.expanduser('~') to get HOME.
        if self['HOME'] != os.path.expanduser('~'):
            echo0("[moreplatform] Warning:")
            echo0('  HOME="%s"' % (self['HOME']))
            echo0('  != os.path.expanduser("~")="%s"'
                  % (os.path.expanduser('~')))

        user_dir_name = os.path.split(self['HOME'])[1]
        # ^ may differ from os.getlogin() getpass.getuser()
        try:
            # doesn't matter. USER will be used (from env) anyway.
            # May differ if using `su` in a graphical terminal window!
            if hasattr(os, "getlogin"):
                if user_dir_name != os.getlogin():
                    echo1("Verbose warning:")
                    echo1('  USER_DIR_NAME="%s"' % (user_dir_name))
                    echo1('  != os.getlogin()="%s"' % (os.getlogin()))
            else:
                pass
                # echo0("There is no os.getlogin (normally not present for"
                #       " Python 2), so USER_DIR_NAME not validated: %s. Using"
                #       " instead." % USER_DIR_NAME)
        except OSError:
            # os.getlogin() causes:
            # "OSError: [Errno 6] No such device or address"
            # Such as on Python 3.10.6 on Linux Mint 21
            pass

        try:
            import getpass  # optional
            if user_dir_name != getpass.getuser():
                echo1("Verbose warning:")
                echo1('  USER_DIR_NAME="%s"' % (user_dir_name))
                echo1('  != getpass.getuser()="%s"' % (getpass.getuser()))
        except ModuleNotFoundError as ex:
            echo1(str(ex))

        try:
            import pwd  # optional
            if user_dir_name != pwd.getpwuid(os.getuid())[0]:
                echo1("Verbose warning:")
                echo1('  USER_DIR_NAME="%s"' % (user_dir_name))
                echo1('  != pwd.getpwuid(os.getuid())[0]="%s"'
                      % (pwd.getpwuid(os.getuid())[0]))
        except ModuleNotFoundError as ex:
            echo3('Skipping optional dependency: %s' % (ex))

    def init_platform(self, os_name):
        # For semi-standard folders on Windows and Darwin see
        # <johnkoerner.com/csharp/special-folder-values-on-windows-versus-mac/>
        self['PREFIX'] = os.environ.get('PREFIX')
        self['SHORTCUT_EXT'] = "desktop"  # Changed in most cases below

        if os_name != "Windows":
            # Common to any applicable non-Windows OS.
            self['HOME'] = os.environ['HOME']
            self['DESKTOP'] = os.path.join(self['HOME'], "Desktop")
            self['DOCUMENTS'] = os.path.join(self['HOME'], "Documents")
            self['PICTURES'] = os.path.join(self['HOME'], "Pictures")
        if os_name == "Windows":
            self['SHORTCUT_EXT'] = "bat"
            self['HOME'] = os.environ['USERPROFILE']
            self['PROFILES'] = os.environ.get("PROFILESFOLDER")
            self['USER'] = os.environ.get("USERNAME")
            self['DESKTOP'] = os.path.join(self['HOME'], "Desktop")
            _od = os.path.join(self['HOME'], "OneDrive")
            _od_desktop = os.path.join(_od, "Desktop")
            _od_documents = os.path.join(_od, "Documents")
            _od_pictures = os.path.join(_od, "Pictures")
            if (not os.path.isdir(self['DESKTOP'])
                    and os.path.isdir(_od_desktop)):
                self['DESKTOP'] = _od_desktop
            self['DOCUMENTS'] = os.environ.get("MYDOCUMENTS")
            if not self['DOCUMENTS']:
                self['DOCUMENTS'] = os.environ.get("MYDOCS")
            if not self['DOCUMENTS']:
                self['DOCUMENTS'] = os.path.join(self['HOME'], "Documents")
                if (not os.path.isdir(self['DOCUMENTS'])
                        and os.path.isdir(_od_documents)):
                    self['DOCUMENTS'] = _od_documents
            self['PICTURES'] = os.path.join(self['HOME'], "Pictures")
            if (not os.path.isdir(self['PICTURES'])
                    and os.path.isdir(_od_pictures)):
                self['PICTURES'] = _od_pictures

            self['SHORTCUTS'] = self['DESKTOP']
            # 'SHORTCUTS' was formerly 'SHORTCUTS_DIR'
            self['APPDATA'] = os.environ['APPDATA']
            self['LOCALAPPDATA'] = os.environ['LOCALAPPDATA']  # formerly local
            self['PROGRAMS'] = os.path.join(self['LOCALAPPDATA'], "Programs")
            self['CACHES'] = os.path.join(self['LOCALAPPDATA'], "Caches")
            self['USER_PROGRAMS'] = os.path.join(self['LOCALAPPDATA'],
                                                 "Programs")
            # self['TMP'] = os.environ.get("TMPDIR")
            # if not self['TMP']:
            #     self['TMP'] = os.environ.get("TEMP")
            # TODO: ^ Ok on Windows 11. Test on Windows 7 before uncommenting
            # if not self['TMP']:
            os.path.join(self['LOCALAPPDATA'], "Temp")
            if self['PREFIX'] is None:
                self['PREFIX'] = self['LOCALAPPDATA']
            self['PIXMAPS'] = self['PREFIX']
            self['LOGS'] = os.path.join(self['LOCALAPPDATA'])  # , "logs")

        elif os_name == "Darwin":
            # See <https://developer.apple.com/library/archive/
            #   documentation/MacOSX/Conceptual/BPFileSystem/Articles/
            #   WhereToPutFiles.html>
            self['PROFILES'] = "/Users"
            self['SHORTCUT_EXT'] = "command"
            # See also <https://github.com/Hierosoft/world_clock>

            self['SHORTCUTS'] = self['DESKTOP']
            # APPDATA = os.path.join(self['HOME'], "Library", "Preferences")
            # ^ Don't use Preferences: It only stores plist format files
            #   generated using the macOS Preferences API.
            # APPDATA = "/Library/Application Support" # .net-like
            self['APPDATA'] = os.path.join(
                self['HOME'],
                ".config"
            )  # .net Core-like
            self['LOCALAPPDATA'] = os.path.join(self['HOME'], ".local",
                                                "share")  # .net Core-like
            ''' TODO: Consider:
            According to <https://forum.unity.com/threads/
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
            self['CACHES'] = os.path.join(self['HOME'], "Library",
                                          "Caches")  # .net Core-like
            # ^ APPDATA & LOCALAPPDATA & CACHES can also be in "/" not HOME
            #   (.net-like)
            self['TMP'] = os.environ.get('TMPDIR')
            # ^ See osxdaily.com/2018/08/17/where-temp-folder-mac-access/
            if not self['TMP']:
                self['TMP'] = os.path.join(self['CACHES'], "tmp")
            # self['PROGRAMS'] = os.path.join(self['HOME'], "Applications")
            # ^ Should only be used for Application Bundle, so:
            self['PROGRAMS'] = os.path.join(self['HOME'], ".local", "lib")
            self['USER_PROGRAMS'] = os.path.join(self['HOME'], ".local", "lib")
            if not self['PREFIX']:
                self['PREFIX'] = os.path.join(self['HOME'], "Library")
                # TODO: ^ Is there something better?
            self['LOGS'] = os.path.join(self['HOME'], "Library", "Logs")
            # ^ Ensure LOGS is ok to be written manually & unstructured since
            #   <https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/MacOSXDirectories/MacOSXDirectories.html>  # noqa: E501
            #   says, ". . . Users can also view these logs using the
            #   Console app."
        else:
            # Linux-like
            # CommonApplicationData = "/usr/share"
            # CommonTemplates = "/usr/share/templates"

            self['PROFILES'] = "/home"  # formerly profiles

            self['SHORTCUTS'] = os.path.join(self['HOME'], ".local", "share",
                                             "applications")

            # region based on <developers.redhat.com/blog/2018/11/07
            #   /dotnet-special-folder-api-linux>
            # _LOCALAPPDATA = os.environ.get('XDG_DATA_HOME')
            # if not _LOCALAPPDATA:
            #     _LOCALAPPDATA = _default_localappdata  # ~/.local/share
            # _APPDATA = os.environ.get('XDG_CONFIG_HOME')
            # if not _APPDATA:
            #     _APPDATA = os.path.join(self['HOME'], ".config")
            # endregion

            self['APPDATA'] = os.path.join(self['HOME'], ".config")
            self['LOCALAPPDATA'] = os.path.join(self['HOME'], ".local",
                                                "share")  # .net-like
            self['CACHES'] = os.path.join(self['HOME'], ".cache")
            self['PROGRAMS'] = os.path.join(self['HOME'], ".local", "lib")
            # ^ or /usr/local/lib
            self['USER_PROGRAMS'] = os.path.join(self['HOME'], ".local", "lib")
            # ^ or os.path.join(self['HOME'], ".local", "share") maybe??
            self['TMP'] = "/tmp"
            if not self['PREFIX']:
                self['PREFIX'] = os.path.join(self['HOME'], ".local")
            self['LOGS'] = os.path.join(self['HOME'], ".var", "log")
            # 'LOGS' was formerly logsDir

        # Any OS:

        if not self['PROFILES']:
            self['PROFILES'] = os.path.dirname(self['HOME'])

        self['SHARE'] = self['LOCALAPPDATA']
        # ^ synonymous; generally written once (during install) if not Windows

        if not self.get('PIXMAPS'):
            self['PIXMAPS'] = os.path.join(self['SHARE'], "pixmaps")

        if not sysdirs.get('USER'):
            # self['USER'] = os.environ.get("USER")
            # try:
            #     self['USER'] = os.getlogin()
            # except OSError:
            # ^ getlogin may differ if using `su` in a graphical terminal!
            if os_name == "Windows":
                self['USER'] = os.environ.get("USERNAME")
            else:
                self['USER'] = os.environ.get("USER")
            # "OSError: [Errno 6] No such device or address"
            #   can happen for some reason with Python 3.10.12
            #   on Linux Mint 21.3
            if not self['USER']:
                print("Warning: couldn't detect USER.", file=sys.stderr)

        if not sysdirs.get('PROFILESFOLDER'):
            self['PROFILESFOLDER'] = os.path.dirname(self['HOME'])

        self['LOCAL_BIN'] = \
            os.path.join(self['PREFIX'], "bin")  # formerly localBinPath
        for key, value in self.items():
            assert value is not None

    def init_cloud(self):
        # self['HOME'] = None  # formerly profile
        # myLocal = None
        # replacements = None  # uh oh, this was None. See substitutions.

        self['CLOUD_NAME'] = None  # formerly myCloudName
        self['CLOUD'] = None  # formerly myCloudPath

        cloud_dir_names = ["Nextcloud", "ownCloud", "owncloud",
                           "OneDrive"]

        for try_cloud_name in cloud_dir_names:
            # ^ The first one must take precedence if more than one exists!
            _try_cloud_path = os.path.join(self['HOME'], try_cloud_name)
            if os.path.isdir(_try_cloud_path):
                self['CLOUD_NAME'] = try_cloud_name
                self['CLOUD'] = _try_cloud_path
                echo1('* detected "%s"' % (self['CLOUD']), multiline=False)
                break
            del _try_cloud_path

            # NOTE: PATH isn't necessary to split with os.pathsep (such
            #   as ":", not os.sep or os.path.sep such as "/") since
            #   sys.path is split already.

        self['CLOUD_PROFILE'] = None  # formerly myCloudProfile;
        # ^ such as ~/Nextcloud/profile formerly ~/Nextcloud/HOME
        # myCloudDir = None

    def check_cloud(self, cloud_path=None, cloud_name=None):
        '''Check for "HOME" directory in cloud path (such as ~/Nextcloud)
        It will not modify the global detected myCloudPath nor myCloudName
        (if not present, both are None) unless you specify a cloud_path.

        Update the substitutions if the cloud exists or is specified,
        whether or not a "HOME" folder exists there.

        Args:
            cloud_path (str, optional): Set the global myCloudPath. (If
                None, use the one discovered on load, that being any
                subfolders in Home named using any string in the global
                CLOUD_DIR_NAMES).
            cloud_name (str, optional): Set the global cloud name (If None,
                use the folder name of cloud_path if cloud_path was set).
                This will only be set if cloud_path is also set.
        '''
        if cloud_path is not None:
            self['CLOUD'] = cloud_path
            if cloud_name is not None:
                self['CLOUD_NAME'] = cloud_name
            else:
                self['CLOUD_NAME'] = os.path.split(cloud_path)[1]

        if self.get('CLOUD') is not None:
            # Update substitutions whether or not the HOME path exists:
            if self['CLOUD'] is not None:
                self._substitutions['%CLOUD%'] = self['CLOUD']
                self._substitutions['$CLOUD'] = self['CLOUD']
            # Set the HOME path if it exists:
            try_cloud_profile_dir = os.path.join(self['CLOUD'], "profile")
            # ^ Yes, LITERALLY a subdir named "profile",
            #   not profile variable.
            if os.path.isdir(try_cloud_profile_dir):
                self['CLOUD_PROFILE'] = try_cloud_profile_dir
            else:
                print('  * Manually create "%s" to enable cloud saves.'
                      % (try_cloud_profile_dir))


sysdirs = PlatformReadOnlyDict()  # Call .readonly() after vars are set below.
sysdirs.init_platform(platform.system())
sysdirs.sanity_check()
sysdirs.init_cloud()
sysdirs.check_cloud()
sysdirs.readonly()
