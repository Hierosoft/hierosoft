# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import shlex

MODULE = os.environ.get('MODULE')

if MODULE is None:
    MODULE = "hierosoft"

from hierosoft import (  # noqa E402
    echo0,
    write0,
    which,
    run_and_get_lists,
    join_if_exists,
    get_pyval,
)

POST_MSG = ('The version in version.py should be changed to the actual'
            ' version before a release, and if version.py is right, then'
            ' a tag matching that should be added to git for the release.')


def main():
    GIT = which("git")
    echo0('* trying to detect version of repo...')
    if GIT is None:
        echo0("Error: The git command must be installed"
              " but it was not in the PATH.")
        return 1

    repo_path = os.getcwd()
    if not os.path.isdir(MODULE):
        echo0('Error: There is no "{}" directory in {}.'
              ' This script must run directly from the repo.'
              ''.format(MODULE, repo_path))
        return 3

    version_py_rel = os.path.join(MODULE, "version.py")

    setup_py_path = os.path.join(repo_path, "setup.py")
    version_pys = [version_py_rel, "setup.py"]
    good_version_py = join_if_exists(repo_path, version_pys)

    if good_version_py is None:
        echo0('Error: No files like {} are in "{}".'
              ' The file should contain VERSION = "x.0.0"'
              ' where "x.0.0" is a version string.'
              ''.format(version_pys, repo_path))
    else:
        write0('"{}" says:'.format(good_version_py))
        echo0(get_pyval('version', good_version_py))
        others = version_pys.copy()
        # version_pys.remove(good_version_py)  # doesn't work, not rel
        count = 0
        for other in others:
            try_path = os.path.join(repo_path, other)
            if try_path == good_version_py:
                # join_if_exists already accounted for this one.
                continue
            if os.path.isfile(try_path):
                count += 1
                echo0('Error: "{}" was already found'
                      ' but there is also a "{}".'
                      ''.format(good_version_py, other))
        if count > 0:
            echo0("- Only one should exist from {}".format(version_pys))
            return count
    echo0('* trying to get version using git...')
    # echo0('checking "{}"...'.format(repo_path))
    if repo_path != os.getcwd():
        raise RuntimeError(
            'Error: repo_path=="{}" but os.getcwd()=="{}"'
            ''.format(repo_path, os.getcwd())
        )
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
                  "".format(describe_cmd_parts, line))
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
        echo0('(There are no tags in "{}")'.format(repo_path))
        return git_code
    if VERSION is None:
        echo0("Warning: 'git describe --tags --abbrev=0' got nothing."
              " Remember to do git pull after you add it online.")
        if not os.path.isfile(version_py_rel):
            echo0("There is currently no \"$MODULE/version.py\".")
        else:
            echo0("Currently \"$MODULE/version.py\" says: ")
            with open(version_py_rel, 'r') as f:
                for rawL in f:
                    echo0(rawL.rstrip())

        echo0("Before adding a tag, $MODULE/version.py should have"
              " the version of the tag you are going to add.")
        return 2

    echo0("{}:".format(version_py_rel))
    with open(version_py_rel, 'r') as f:
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
    echo0()
    echo0(POST_MSG)
    echo0()


if __name__ == "__main__":
    sys.exit(main())
