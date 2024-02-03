#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #!/usr/bin/python3
# based on EnlivenMinetest/utilities/install-lmk
#
# The copy in hierosoft is relicensed by Poikilos (original author)
# under license of hierosoft
'''
install-lmk
-----------
Use any "minetest" folder under the current working directory
to install or upgrade.

Developers: If /opt/minebest/mtkit is present, that will be used.

See hierosoft.hminetestsrc documentation for more info.
'''
import re
import sys
import os

scripts_dir = os.path.dirname(os.path.realpath(__file__))
repo_dir = os.path.dirname(scripts_dir)
repos_dir = os.path.dirname(repo_dir)
try_other_repo = os.path.join(repos_dir, "hierosoft")
good_h_flag = os.path.join(try_other_repo, "hierosoft", "__init__.py")
if os.path.isfile(good_h_flag):
    sys.path.insert(0, try_other_repo)
    print("Using {}".format(try_other_repo), file=sys.stderr)
else:
    print("No {}. Trying installed copy...".format(good_h_flag),
          file=sys.stderr)

# if os.path.isfile(os.path.join(repos_dir, "hierosoft", "init.py")):
#     sys.path.insert(repos_dir)
# ^ implies both are installed (and that repos_dir is actually modules_dir),
#   so leave path alone.

from hierosoft.hminetestsrc import main  # noqa E402

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
