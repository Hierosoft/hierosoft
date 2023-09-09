#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from hierosoft.gui_tk import main as gui_main
from hierosoft.moreweb.hierosoftupdate import main as update_main
import re


def main():
    prefix = "[main] "
    enable_web = True
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    for i, arg in enumerate(sys.argv):
        if i < 1:
            continue  # skip the command itself
        if arg == "--offline":
            enable_web = False
    if enable_web:
        print(prefix+"Running with web...", file=sys.stderr)
        sys.exit(update_main())
    else:
        print(prefix+"Running without web...", file=sys.stderr)
        sys.exit(gui_main())


if __name__ == "__main__":
    sys.exit(main())
