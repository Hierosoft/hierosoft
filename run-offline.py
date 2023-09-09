#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re

from run import main

WANT_WEB = False

if __name__ == "__main__":
    disable_web_index = None
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    for i, arg in enumerate(sys.argv):
        if i < 1:
            continue  # skip the command itself
        if arg == "--offline":
            disable_web_index = i
    if disable_web_index:
        if WANT_WEB:
            del sys.argv[disable_web_index]
    else:
        if not WANT_WEB:
            sys.argv.append("--offline")
    sys.exit(main())