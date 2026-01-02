#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import platform
import re
import shutil
import sys

from hierosoft import ALREADY_LAUNCHED


dst_python_scripts = os.path.dirname(sys.executable)
dst_python_env = os.path.dirname(dst_python_scripts)
if os.path.isfile(os.path.join(dst_python_env, "pyvenv.cfg")):
    # Copy TCL to venv to avoid Windows bug
    # "Can't find a usable init.tcl in the following directories"
    # (See <https://stackoverflow.com/a/30377257/4541104>)
    dst_tcl = os.path.join(dst_python_env, "tcl")
    if ((not os.path.isdir(dst_tcl)) and (sys.version_info.major < 3)
            and (platform.system() == "Windows")):
        good_tcl = None
        for src_python_lib in sys.path:
            src_python_dir = os.path.dirname(src_python_lib)
            src_tcl = os.path.join(src_python_dir, "tcl")
            if os.path.isdir(src_tcl):
                good_tcl = src_tcl
                sys.stderr.write("cp -R {} {} # ..."
                                 .format(repr(src_tcl), repr(dst_tcl)))
                sys.stderr.flush()
                shutil.copytree(src_tcl, dst_tcl)
                if os.path.splitext(os.path.split(sys.executable)[1])[0].lower() == "python":  # noqa: E501
                    # Using python
                    run_cmd = [sys.executable] + sys.argv
                else:
                    # Using precompiled Python program (Needs testing)
                    run_cmd = sys.argv
                print("OK. Relaunching {}...".format(run_cmd), file=sys.stderr)
                import subprocess
                subprocess.Popen(run_cmd)
                sys.exit(0)
                break
        if not good_tcl:
            print("[run] Warning: no tcl in {}".format(sys.path),
                  file=sys.stderr)
    else:
        print("[run] Using {}".format(dst_tcl))


def main():
    prefix = "[main] "
    enable_web = True
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    for i, arg in enumerate(sys.argv):
        if i < 1:
            continue  # skip the script (not an arg)
        if arg == "--offline":
            enable_web = False
        elif arg == ALREADY_LAUNCHED:
            enable_web = False
    print("[run main] Ran as: {}".format(" ".join(sys.argv)))
    if enable_web:
        from hierosoft.moreweb.hierosoftupdate import main as update_main  # noqa: E402,E501
        print(prefix+"Running with web...", file=sys.stderr)
        sys.exit(update_main())
    else:
        from hierosoft.gui_tk import main as gui_main  # noqa: E402
        print(prefix+"Running without web...", file=sys.stderr)
        sys.exit(gui_main())


if __name__ == "__main__":
    sys.exit(main())
