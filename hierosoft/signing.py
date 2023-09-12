# -*- coding: utf-8 -*-
"""
Detect files that need to be signed and call an available signtool.
"""
from __future__ import print_function
import os
import sys
import shlex
from getpass import getpass
import glob
import platform
import subprocess

PLATFORM_BITS = 64
if platform.architecture()[0] == "32bit":
    PLATFORM_BITS = 32
SYSTEM = platform.system()

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
# ^ This is ok since this file won't need to run from a PyInstaller exe
ASSETS_DIR = os.path.join(MODULE_DIR, "assets")
DATA_DIR = os.path.join(ASSETS_DIR, "data")

def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if sys.version_info.major < 3:
    input = raw_input

SIGN_CMD_FMT = (
    "{signtool} sign /tr {timestamp_server} /td sha256 /fd sha256 /a {sign_this_file}"
    # "{signtool} /P {password} /TR {timestamp_server} /a {sign_this_file}"
    # "{signtool} /F {pfx_path} /P {password} /TR {timestamp_server} {sign_this_file}"
    # ^ /T is deprecated. See doc/development/signing.md.
    # ^ /F may not be necessary. PFX can be generated from PVK/other format
    # ^ /debug would have to go directly after "sign" to diagnose failures.
)
# ^ such as `SIGNTOOL.EXE /F tcs.pfx /P <password>
# Sectigo support says:
# - signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a "c:\path\to\file_to_sign.exe"
# - <https://sectigo.com/resource-library/time-stamping-server>
# - <https://docs.microsoft.com/en-us/windows/win32/appxpkg/how-to-sign-a-package-using-signtool>


KNOWN_SIGNTOOLS_PER_SYSTEM = {}

# ^ Potentially returns:
#   ('64bit', 'WindowsPE')  # on Windows 10 Home upgrade from 7 Home OEM
#   ('64bit', 'ELF')  # on Linux Mint 21 64-bit Desktop

_signtool_list_name = (
    "signtools.{}.{}.list".format(platform.system(), PLATFORM_BITS)
)
_signtool_list_file = os.path.join(DATA_DIR, _signtool_list_name)
if os.path.isfile(_signtool_list_file):
    with open(_signtool_list_file, 'r') as f:
        for rawL in f:
            line = rawL.strip()
            if len(line) == 0:
                continue
            if line.startswith("#"):
                continue
            if KNOWN_SIGNTOOLS_PER_SYSTEM.get(SYSTEM) is None:
                KNOWN_SIGNTOOLS_PER_SYSTEM[SYSTEM] = []
            KNOWN_SIGNTOOLS_PER_SYSTEM[SYSTEM].append(line)

KNOWN_SIGNTOOLS = KNOWN_SIGNTOOLS_PER_SYSTEM.get(SYSTEM)
SIGNTOOL = None
if KNOWN_SIGNTOOLS is not None:
    for KNOWN_SIGNTOOL in KNOWN_SIGNTOOLS:
        if os.path.isfile(KNOWN_SIGNTOOL):
            SIGNTOOL = KNOWN_SIGNTOOL
            break
    del KNOWN_SIGNTOOL


def main():
    if KNOWN_SIGNTOOLS is None:
        raise NotImplementedError(
            "A known signtools list isn't implemented for {}.{}"
            "".format(SYSTEM, PLATFORM_BITS)
        )

    if SIGNTOOL is None:
        echo0("A sign tool was expected to be installed such as:")
        for line in KNOWN_SIGNTOOLS:
            echo0('- "{}"'.format(line))
        raise FileNotFoundError(
            "No known {} {} signtool is installed."
            "".format(SYSTEM, PLATFORM_BITS)
        )
    options = {
        'timestamp_server': "http://timestamp.sectigo.com"
        # ^ formerly "http://timestamp.comodoca.com", now a documentation alias
    }
    option_keys = {  # Make every key all caps and check all caps arg against it
        "/P": "password",
        "/F": "pfx_path",
        # "/T": "timestamp_server",  # deprecated see doc/development/signing.md
        "/TR": "timestamp_server",
    }
    key = None
    for argi in range(1, len(sys.argv)):
        arg = sys.argv[argi]
        if key is not None:
            options[key] = arg
            key = None
        else:
            key = option_keys.get(arg)
            if key is not None:
                continue
            if options.get('sign_this_file') is not None:
                echo0("Only one of {} followed by a value"
                      " or one sign_this_file was expected but got: {}"
                      "".format(option_keys.keys(), arg))
                return 1
            options['sign_this_file'] = arg
    echo0()
    echo0()
    echo0("Before you continue:")
    echo0("1. The SafeNet USB key must be inserted")
    echo0("2. You must have the password on hand.")
    echo0(
        "3. You must have installed the SafeNet Authentication Client"
        " from the link sent along with the SafeNet USB key"
        " (To work, this tool must"
        " launch a GUI window via signtool)."
    )
    echo0()
    if options.get('sign_this_file') is None:
        search_dir = os.getcwd()
        # See <https://stackoverflow.com/a/168424>
        wild_path = os.path.join(search_dir, "*.exe")
        files = list(filter(os.path.isfile, glob.glob(wild_path)))
        files.sort(key=lambda x: os.path.getmtime(x))
        default_sign_this_file = files[-1]  # last one [-1] is latest
        options['sign_this_file'] = input(
            'A file wasn\'t specified. What file would you like to sign [{}]? '
            ''.format(default_sign_this_file)
        )
        if options['sign_this_file'].strip() == "":
            options['sign_this_file'] = default_sign_this_file
    else:
        echo0('The specified sign_this_file will be signed: "{}"'
              ''.format(options['sign_this_file']))
    echo0("options={}".format(options))
    '''
    if options.get('password') is None:
        options['password'] = getpass(
            "Enter the Sectigo Token Password"
            " (not same as login password or blank to quit): "
        )
        if options.get('password') == "":
            echo0("The operation was cancelled by the user.")
            return 1
    if options.get('password') == "":
        echo0("The password must not be blank"
              " because the real Sectigo password wouldn't be.")
        return 1
    '''

    this_sign_cmd_fmt = SIGN_CMD_FMT
    '''
    if options.get('pfx_path') is not None:
        this_sign_cmd_fmt += " /F {pfx_path}"
    else:
        pass
        # echo0('You must specify a pfx_path via /F')
        # return 1
    '''
    sign_cmd = this_sign_cmd_fmt.format(
        signtool=SIGNTOOL,
        # pfx_path=options['pfx_path'],
        # password=options.get('password'),
        timestamp_server=options.get('timestamp_server'),
        sign_this_file=options['sign_this_file'],
    )
    echo0("Running '{}'...".format(sign_cmd))
    proc = subprocess.Popen(
        sign_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    (result, err) = proc.communicate()
    if result is not None:
        print(result.decode('utf-8'))
    if err is not None:
        print(err.decode('utf-8'), file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
