#!/usr/bin/env python
from __future__ import print_function
import sys

import os

verbose = 0
for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
    if arg.startswith("--"):
        if arg == "--verbose":
            verbose = 1
        elif arg == "--debug":
            verbose = 2


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def echo1(*args, **kwargs):
    if not verbose:
        return
    print(*args, file=sys.stderr, **kwargs)


def echo2(*args, **kwargs):
    if verbose < 2:
        return
    print(*args, file=sys.stderr, **kwargs)


def get_verbose():
    return verbose


def set_verbose(enable_verbose):
    global verbose
    if (enable_verbose is not True) and (enable_verbose is not False):
        vMsg = enable_verbose
        if isinstance(vMsg, str):
            vMsg = '"{}"'.format(vMsg)
        raise ValueError(
            "enable_verbose must be True or False not {}."
            "".format(vMsg)
        )
    verbose = enable_verbose


def get_subdir_names(folder_path, hidden=False):
    ret = []
    if os.path.exists(folder_path):
        ret = []
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if ((hidden or sub_name[:1]!=".") and
                    (os.path.isdir(sub_path))):
                ret.append(sub_name)
    return ret


def get_file_names(folder_path, hidden=False):
    ret = None
    if os.path.exists(folder_path):
        ret = []
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if ((hidden or sub_name[:1]!=".") and
                    (os.path.isfile(sub_path))):
                ret.append(sub_name)
    return ret


def get_ext(filename):
    ext = ""
    dot_i = filename.rfind('.')
    if dot_i > -1:
        ext = filename[dot_i+1:]
    return ext


# program_name is same as dest_id
def get_installed_bin(programs_path, dest_id, flag_names):
    # found = False
    ret = None
    versions_path = programs_path
    for flag_name in flag_names:
        installed_path = os.path.join(versions_path, dest_id)
        flag_path = os.path.join(installed_path, flag_name)
        if os.path.isfile(flag_path):
            # found = True
            ret = flag_path
            # print("    found: '" + flag_path + "'")
            break
        else:
            pass
            # print("    not_found: '" + flag_path + "'")
    return ret


def is_installed(programs_path, dest_id, flag_names):
    path = get_installed_bin(programs_path, dest_id, flag_names)
    return (path is not None)



if __name__ == "__main__":
    print("You must import this module and call get_meta() to use it"
          "--maybe you meant to run update.pyw")
