#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from hierosoft.gui_tk import main
import re

if __name__ == "__main__":
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
