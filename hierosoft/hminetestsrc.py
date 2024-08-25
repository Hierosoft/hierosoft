#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
install-lmk <project name> [--from <built dir>] [options]

The available project names are:
classic (or final or minetest) to install ~/minetest-rsync,
finetest (or fine) to install ~/finetest-rsync
    (for the game that ripped off Multicraft.org's name), or
trolltest (or troll) to install ~/trolltest-rsync (based on MT5).

If the current directory is not ~/minetest-rsync, the suffix "local"
will be used for installed directories and shortcuts instead of rsync to
indicate you are using a downloaded copy (not using a copy obtained via
rsync access to the build server).

Options:
--from <built dir>    Install from this directory. Defaults to
                      "/opt/minebest/mtkit/minetest" (from home not opt
                      if using Windows).
--server              Require a binary ending with "server" to be
                      present in built dir. Defaults to False.
--client              Require a binary ending with "server" to be
                      present in built dir. Defaults to True, but False
                      if --server is used without --client.
"""
from __future__ import print_function
import copy
import json
import os
import platform
# import shlex
# import shutil
# import stat
import sys

# if __name__ == "__main__":
#     submodule_dir = os.path.dirname(os.path.realpath(__file__))
#     module_dir = os.path.dirname(submodule_dir)
#     repo_dir = os.path.dirname(module_dir)
#     repos_dir = os.path.dirname(repo_dir)
#     if os.path.isfile(os.path.join(repos_dir,
#                                    "hierosoft", "hierosoft", "init.py")):
#         sys.path.insert(repos_dir)

from hierosoft import (
    sysdirs,
    echo0,
    write0,
    # get_happ_path,
)

from hierosoft.morelogging import hr_repr

# from hierosoft.moreplatform import (
#     get_dir_size,
# )

from hierosoft import (
    # rewrite_conf_str,
    generate_caption,
)

from hierosoft.hinstaller import (
    HInstaller,
    # console_callback,
)

from hierosoft import hminetest

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    ModuleNotFoundError = ImportError

INSTALL_SRC = os.path.join("/opt", "minebest", "mtkit", "minetest")
if platform.system() == "Windows":
    INSTALL_SRC = os.path.join(sysdirs['HOME'], "minebest", "mtkit",
                               "minetest")
# ^ Changed later if detected in current dir (in use_if_source).
DETECT_KIT_SUBDIRS = ["minetest", "mtsrc"]  # Use via detect_source
# ^ First entry of DETECT_KIT_SUBDIRS has to be the new INSTALL_SRC!

VARIANT = "rsync"  # ^ Changed to "local" if not in default INSTALL_SRC
# - "local" copy of linux-minetest-kit.zip is for end users
# - "rsync" copy from /opt/minebest/ is for maintainers
#   (linux-minetest-kit.zip is built by /assemble/util/buildskipwin.sh
#   and then must be manually extracted to /opt/minebest/mtkit)

arg_project_name = {
    # 'final': "classic",
    'classic': "classic",
    'trolltest': "trolltest",
    # 'troll': "trolltest",
    'finetest': "finetest",
    # 'fine': "finetest",
}


def usage():
    echo0(__doc__)


def detect_source(path):
    """Get a built minetest directory inside of path if present.
    It must contain all DETECT_KIT_SUBDIRS for the subdirectory to be
    detected.

    Returns:
        str: minetest subdirectory. If path does not have
            all DETECT_KIT_SUBDIRS, result is None.
    """
    for sub in DETECT_KIT_SUBDIRS:
        sub_path = os.path.join(path, sub)
        if not os.path.isdir(sub_path):
            return None
    return os.path.join(path, DETECT_KIT_SUBDIRS[0])


def use_if_source(path):
    """Use the path as INSTALL_SRC if it contains a minetest install.
    See detect_source for details. A message is shown regarding the
    status.

    Affects globals:
    - INSTALL_SRC
    - VARIANT

    Returns:
        bool: True if is a source (even if INSTALL_SRC is already the
            same).
    """
    global INSTALL_SRC
    global VARIANT
    detected_src = detect_source(path)
    if detected_src:
        if detected_src != INSTALL_SRC:
            echo0('Switching from "{}" to local copy:'
                  '\n  "{}"'
                  ''.format(INSTALL_SRC, detected_src))
            INSTALL_SRC = detected_src
            VARIANT = "local"
        else:
            echo0('Using standard source location (same as current dir):'
                  '\n  "{}"'
                  ''.format(INSTALL_SRC))
        return True
    else:
        echo0('Using standard source location'
              ' (since current dir does not have both "mtsrc and "minetest"):'
              '\n  "{}"'
              ''.format(INSTALL_SRC))
    return False


def main():
    prefix = "[main] "
    use_if_source(os.getcwd())
    required_bin_suffixes = None
    why_meta = "detected"
    project_meta = hminetest.detect_project_meta(INSTALL_SRC)
    if project_meta is None:
        why_meta = "undetected"
    key_arg = None
    install_from = None
    project_name = None
    if len(sys.argv) < 2:
        usage()
        if project_meta is None:
            echo0("Error: You must specify one of the names above"
                  " unless well-known executable files can be detected"
                  " to determine what project is being installed.")
            return 1
        else:
            echo0("using detected project: {}".format(
                json.dumps(project_meta, indent=2, sort_keys=True),
            ))
            # NOTE: ^ shows name_and_variant_fmt with literal "{}" still
            #   (unavoidable without messing with it), so see
            #   "Name={}" further down for that output (Only possible
            #   after `variant` is set).
    elif len(sys.argv) == 2:
        pass  # 1st arg (arg [1]) is always handled further down
    else:
        for arg_i in range(2, len(sys.argv)):
            arg = sys.argv[arg_i]
            if key_arg is not None:
                if arg.startswith("--"):
                    usage()
                    echo0("Error: {} must be followed by a value but got {}."
                          "".format(key_arg, arg))
                    return 1
                if key_arg == "--from":
                    install_from = arg
                else:
                    usage()
                    echo0("Error: unknown argument {}".format(key_arg))
                    return 1
            elif arg == "--server":
                if required_bin_suffixes is None:
                    required_bin_suffixes = ["server"]
                else:
                    required_bin_suffixes.append("server")
            elif arg == "--client":
                if required_bin_suffixes is None:
                    required_bin_suffixes = [""]
                else:
                    required_bin_suffixes.append("")
            elif arg == "--from":
                key_arg = arg
            else:
                usage()
                echo0('Error: The 2nd argument must be "server" or left out')
                return 1
    if key_arg is not None:
        usage()
        echo0("Error: {} must be followed by a value."
              "".format(key_arg))
        return 1

    if len(sys.argv) > 1:
        name_arg = sys.argv[1]
        project_name = arg_project_name.get(name_arg)
        if project_name is None:
            raise ValueError(
                "Got %s but expected one from %s"
                % (
                    hr_repr(name_arg),
                    hr_repr(list(arg_project_name.keys()))
                )
            )
        if project_meta is not None:
            echo0(prefix+"reverting detected meta due to %s argument."
                  % hr_repr(name_arg))
            project_meta = None
            why_meta = "cleared by %s argument" % name_arg
    elif project_meta is not None:
        project_name = project_meta.get('project_name')
        # ^ May differ from name. For example, project name for
        #   Final Minetest is "classic".
        echo0(prefix+"detected %s" % project_name)

    if install_from is None:
        install_from = INSTALL_SRC

    if required_bin_suffixes is None:
        required_bin_suffixes = [""]  # only check for * not *server
        # when no options were specified.
        echo0("Warning: No --client or --server option was set, and"
              " source was %s so only client binary will be verified"
              " to exist."
              % why_meta)

    if project_meta is None:
        if project_name is None:
            raise ValueError(
                "You must either specify one of %"
                " or the source must be a well-known project that can be"
                " detected."
                % hr_repr(list(hminetest.project_metas.keys()))
            )
        project_meta = hminetest.project_metas[project_name]
        project_meta['required_relpaths'] = []
        for relpath in project_meta['shortcut_exe_relpaths']:
            for suffix in required_bin_suffixes:
                # for each file such as suffix "" for minetest and
                #   suffix "server" for minetestserver, add to required
                #   files if specified (Instead of if exists, which
                #   only is behavior on detect, though in both cases
                #   they are verified to exist before install, later).
                try_relpath = relpath + suffix
                project_meta['required_relpaths'].append(try_relpath)
        echo0("Generated relpaths: %s"
              % hr_repr(project_meta['required_relpaths']))
    else:
        if project_meta.get('required_relpaths') is None:
            raise NotImplementedError(
                "Project %s was detected but required_relpaths was not set."
                % hr_repr(project_meta.get('project_name'))
            )
        if len(project_meta['required_relpaths']) == 0:
            raise FileNotFoundError(
                "None of the well-known executables for %s could be found: %s"
                % (
                    project_name,
                    hr_repr(project_meta.get('shortcut_exe_relpaths'))
                )
            )
    project_meta['build_options'] = set()
    for required_bin_suffix in required_bin_suffixes:
        if required_bin_suffix == "":
            project_meta['build_options'].add("--client")
        elif required_bin_suffixes == "server":
            project_meta['build_options'].add("--server")
    # A set is not serializable, so:
    project_meta['build_options'] = list(project_meta['build_options'])
    # 'dirname': If None, it will become the default. Defaults to
    #     project_name + "-" + VARIANT (such as minetest-rsync). If
    #     VARIANT is blank or None, the variant_dirname will become the
    #     same as the dirname (such as minetest).
    # VARIANT (str): Append this to the dirname. It also
    #     affects the shortcut--see "variant" under install_shortcut in
    #     hierosoft.moreplatform.
    #
    #     On desktops environments following the XDG standard,
    #     also appended to the icon filename so the variant's can
    #     co-exist with other variants (such as deb and AppImage and
    #     so on). Defaults to VARIANT (which is set automatically to
    #     "rsync" or "local" elsewhere).
    #     - Also used as the special string to put in parenthesis
    #       after the name to denote what kind of package or source was
    #       used to obtain the program, such as "rsync" if a local
    #       custom build, or more commonly "git", "deb", etc. If it is
    #       an official binary archive, set this to "release". However,
    #       if the package type (such as deb) is native to your distro,
    #       set this to None to indicate it is the package supported
    #       for your distro.
    #     - Name is constructed using
    #       project_meta['name_and_variant_fmt'] if present, otherwise
    #       Name will be project_meta['name] + " (" + 'variant' + ")".
    #       If variant is None, name is project_meta['name'].

    project_meta['dirname'] = "{}-{}".format(
        project_meta['dirname'],
        VARIANT
    )
    project_meta['shortcut_namespace'] = "{}-{}".format(
        project_meta['shortcut_namespace'],
        VARIANT
    )  # such as org.minetest.finetest-rsync

    project_meta['shortcut']['Name'] = generate_caption(project_meta, VARIANT)
    detected_luid = project_meta['project_name'] + "-" + VARIANT
    if 'luid' in project_meta:
        echo0("Warning: luid was {} but will be changed to detected {}."
              "".format(project_meta['luid'], detected_luid))
    project_meta['luid'] = detected_luid

    project_meta['organization'] = "minetest.org"

    results = install_minetest(
        install_from,
        project_meta,
    )
    error = results.get('error')
    if error is not None:
        echo0("Error: %s" % error)
    return 0


def install_minetest(src, project_meta, dst=None,
                     overwrite_included_worlds=False, callback=None):
    """Install Minetest.

    Args:
        project_meta (dict[string]): The information necessary
            to install the program. It must have the keys:
            - 'dirname' (Optional[str]): The directory under the
              OS program files (ignored if dst is set).
            - 'required_relpaths' (list): Paths relative to
              src that are required (for ensuring src is intact). It
              can be generated using the detect_project_meta function.
            - There are more required keys for shortcut
              generation (See install_shortcut).
        src (string): The location of the minetest install source to
            copy.
        dst (Optional[string]): Install here. If None, it will become
            the default. Defaults to project_meta['dirname'] placed
            under C:\\games if Windows, otherwise under HOME.
        callback (Optional[callable])): Function to call regarding
            progress. It must accept a dictionary and check the
            following keys:
            - 'error': If set, the operation has failed.
            - 'message': If set, show this message.
            - 'done_bytes': The number of bytes completed so far.
            - 'total_bytes': The estimated total of bytes (Divide
              'done_bytes' by this after casting both to float to
              determine progress ratio).
            - 'status': If 'done' then the process is done.

    Returns:
        dict: "destination" is where it was installed if at all. See
            "warning" in case there was something incorrect about the
            install.
    """
    project_name = project_meta.get('name')
    project_msg = project_name
    if project_msg is None:
        project_msg = hr_repr(project_meta)
    del project_name
    if os.path.isfile(os.path.join(src, ".saved_passwords")):
        raise ValueError("Source should not contain .saved_passwords")

    if os.path.isfile(os.path.join(src, "debug.txt")):
        raise ValueError(
            'Source "{}" should not contain debug.txt. You should build a'
            ' clean copy or remove the file to prevent this error.'
            ''.format("debug.txt")
        )

    src_files = project_meta.get('required_relpaths')
    if src_files is None:
        usage()
        error = ("There are no specified source files for %s"
                 " so whether it is intact can't be checked."
                 "" % hr_repr(project_msg))
        raise NotImplementedError(error)
    elif not src_files:
        raise KeyError("'required_relpaths' was {}."
                       " It must specify at least one executable"
                       " (usually set via detect_project_meta)."
                       "".format(src_files))

    missing_files = []
    for src_file in src_files:
        if not os.path.isfile(os.path.join(src, src_file)):
            missing_files.append(src_file)

    if len(missing_files) > 0:
        error = ("The following files are required to be compiled"
                 " for {} before install but are missing: {}"
                 "".format(project_msg, missing_files))
        error += "\nTry:"
        error += "\nbash -e mtcompile-libraries.sh build"
        build_options = project_meta.get('build_options')
        if not build_options:
            error += "\n#The program build options are unknown. For client do:"
            build_options = ("--client")
        build_options_s = ""
        for build_option in build_options:
            build_options_s += " {}".format(build_option)

        error += ("\nperl mtcompile-program.pl build --{}{}"
                  "".format(project_meta.get('project_name'),
                            build_options_s))
        return {
            'error': error,
        }

    dirname = project_meta['dirname']

    if dst is None:
        if platform.system() == "Windows":
            GAMES = "C:\\games"
            if not os.path.isdir(GAMES):
                os.mkdir(GAMES)
            dst = os.path.join(GAMES, dirname)
        else:
            dst = os.path.join(sysdirs['HOME'], dirname)
    project_meta['dst_path'] = dst  # for 1-file progs use this not dst_dirpath
    project_meta['dst_dirpath'] = dst
    keeps = [  # only add if not in dst
        'arrowkeys.txt',
        'mods',
        'minetest.conf',
        'screenshots',
        'cache',
        # 'games',  # only included games are sync'd (with delete)
        # '.saved_passwords',  # disallowed above
        os.path.join("client", "serverlist", "favoriteservers.txt"),
        # ^ TODO: synchronize favoriteservers.txt on per-server basis
    ]

    worlds = os.path.join(src, "worlds")
    if not overwrite_included_worlds:
        if os.path.isdir(worlds):
            for sub in os.listdir(worlds):
                keeps.append(os.path.join("worlds", sub))
    else:
        pass
        # for sub in os.path.join(src, 'worlds'):
        #     # Overwrite *only all games in* src (keep others in dst!).
        #     replaces.append(os.path.join('worlds', sub))

    replaces = src_files.copy()
    # ^ src_files were already checked above
    replaces.append("release.txt")
    # echo0("{}:".format(src))
    for src_sub in os.listdir(src):
        # echo0('* "{}"'.format(src_sub))
        src_sub_path = os.path.join(src, src_sub)
        if os.path.isfile(src_sub_path):
            continue
        for subsub in os.listdir(src_sub_path):
            # subsub_path = os.path.join(src_sub_path, subsub)
            if src_sub in ("games", "util", "mods", "po",
                           "locale", "clientmods", "builtin"):
                # ^ mods in case MT packager included any mod(s)
                replaces.append(os.path.join(src_sub, subsub))
                # ^ relative, such as games/bucket_game

    dst_games = os.path.join(dst, "games")
    if os.path.isdir(dst_games):
        for sub in os.listdir(dst_games):
            keep = os.path.join("games", sub)
            if keep in replaces:
                # Do not keep games w/ same names as builtin ones
                continue
            keeps.append(keep)

    project_meta['keeps'] = keeps
    project_meta['replaces'] = replaces
    # for k, v in project_meta.items():
    #     write0("project_meta['{}']={}=".format(k, v))
    #     sys.stderr.flush()
    #     echo0(
    #         json.dumps(v, sort_keys=True, indent=2)
    #     )
    # echo0("project_meta={}".format(
    #     json.dumps(project_meta, sort_keys=True, indent=2))
    # )

    installer = HInstaller(
        src,
        dst,
        project_meta,
    )

    if not os.path.isdir(dst):
        write0('Installing %s to %s...'
               % (hr_repr(project_msg), hr_repr(dst)))
    else:
        warning = 'Upgrading "{}".'.format(dst)
        echo0('{}'.format(warning))

    results = installer.install(
        callback=callback,
    )
    installed_meta = copy.deepcopy(installer.meta)
    # if 'replaces' in installed_meta:
    #     del installed_meta['replaces']
    # if 'keeps' in installed_meta:
    #     del installed_meta['keeps']
    echo0("Install finished: {}".format(json.dumps(installed_meta, indent=2,
                                                   sort_keys=True)))
    added_mb = round(installer.bytes_done / 1024.0 / 1024.0, 2)
    removed_mb = round(installer.delete_bytes_total / 1024.0 / 1024.0, 2)
    size_mb = round(installer.meta['size'] / 1024.0 / 1024.0, 2)
    echo0("* {} source file(s) {}mb (plus your old files if any)"
          "".format(installer.file_count, size_mb))
    echo0("* {} added ({}mb)".format(installer.add_count, added_mb))
    echo0("* {} removed ({}mb)".format(installer.deletes_done, removed_mb))
    echo0("* {} already up-to-date".format(installer.match_count))
    return results


# def get_missing_subs(mt_share_path, subs):
#     """Get a list of any missing files for a source *or* destination.
#     """

# if __name__ == "__main__":
#     sys.exit(main())
