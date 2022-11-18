#!/usr/bin/env python
import sys
import os
import shlex

MODULE = os.environ.get('MODULE')

if MODULE is None:
    MODULE = "hierosoft"

from hierosoft import (
    echo0,
    which,
    run_and_get_lists,
)

POST_MSG = ('The version in version.py should be changed to the actual'
            ' version before a release, and if version.py is right, then'
            ' a tag matching that should be added to git for the release.')

def main():
    echo0("* trying to get version using git for $MODULE/version.py...")
    GIT = which("git")
    if GIT is None:
        echo0("Error: The git command must be installed"
              " but it was not in the PATH.")
        return 1

    if not os.path.isdir(MODULE):
        echo0('Error: There is no "{}" directory in {}.'
              ' This script must run directly from the repo.'
              ''.format(MODULE, os.getcwd()))
        return 3

    VERSION_PY = os.path.join(MODULE, "version.py")
    if not os.path.isfile(VERSION_PY):
        echo0('Error: There is no "{}" file in "{}".'
              ' The file should contain VERSION = "x.0.0"'
              ' where "x.0.0" is a version string.'
              ''.format(VERSION_PY, os.getcwd()))
    describe_cmd = "git describe --tags --abbrev=0"
    describe_cmd_parts = shlex.split(describe_cmd)
    git_out, git_err, git_code = run_and_get_lists(describe_cmd_parts)
    VERSION = None
    for rawL in git_out:
        line = rawL.strip()
        if len(line) < 1:
            continue
        if VERSION is None:
            VERSION = line
        else:
            echo0("Error: '{}' returned an unexpected extra line: {}"
                  "".format(line))
    err_count = 0
    for rawL in git_err:
        line = rawL.strip()
        if len(line) < 1:
            continue
        echo0("[check-version] Error: [{}] {}".format(describe_cmd, line))
        err_count += 1
    if git_code != 0:
        if err_count < 1:
            echo0("tag={}".format(VERSION))
            echo0("[check-version] ['{}'] returned code {}"
                  "".format(describe_cmd, git_code))
        echo0('(There are no tags in "{}")'.format(os.getcwd()))
        return git_code
    if VERSION is None:
        echo0("Warning: 'git describe --tags --abbrev=0' got nothing."
              " Remember to do git pull after you add it online.")
        if not os.path.isfile(VERSION_PY):
            echo0("There is currently no \"$MODULE/version.py\".")
        else:
            echo0("Currently \"$MODULE/version.py\" says:")
            with open(VERSION_PY, 'r') as f:
                for rawL in f:
                    echo0(rawL.rstrip())

        echo0("Before adding a tag, $MODULE/version.py should have"
              " the version of the tag you are going to add.")
        return 2




    echo0("{}:".format(VERSION_PY))
    with open(VERSION_PY, 'r') as f:
        for rawL in f:
            echo0(rawL.rstrip())
    echo0()
    echo0()
    echo0()
    echo0("actual version (from git):")
    echo0()
    echo0('VERSION = "{}"'.format(VERSION))
    echo0()
    echo0()
    echo0(POST_MSG)
    echo0()

if __name__ == "__main__":
    sys.exit(main())
