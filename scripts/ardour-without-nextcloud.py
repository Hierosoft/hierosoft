#!/usr/bin/env python3
"""
Typically installed like:
1.
ls ardour-without-nextcloud.py && ln -s `pwd`/ardour-without-nextcloud.py ~/.local/bin/ardour-without-nextcloud
# ^ ls ensures you are in the correct directory, to avoid creating a faulty symlink.
2.
SHORTCUT="$HOME/.local/share/applications/Ardour-Ardour_8.6.0-without-nextcloud.desktop"
cat > $SHORTCUT <<END
[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Terminal=false
Exec=$HOME/.local/bin/ardour-without-nextcloud
Name=Ardour-8.6.0 without Nextcloud
Icon=Ardour-Ardour_8.6.0
Comment=Digital Audio Workstation
Categories=AudioVideo;AudioEditing;Audio;Recorder;
END
3.
chmod +x "$SHORTCUT"

NOTE: Ardour-Ardour_8.6.0-without-nextcloud.desktop has to be a
different filename (not just Name internally) than the system's icon,
otherwise it will hide the system's icon
- However, you may prefer that in this case due to issue between
  Nextcloud and Ardour, so you could name the file
  Ardour-Ardour_8.6.0.desktop
"""
from __future__ import print_function
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(SCRIPTS_DIR)

sys.path.insert(0, REPO_DIR)

from hierosoft.processwrapper import ProcessWrapper  # noqa: E402


def main():
    processwrapper = ProcessWrapper(
        ProcessWrapper.ardour_path,
        find_bin_pattern="ardour",
    )
    return processwrapper.run()


if __name__ == "__main__":
    sys.exit(main())
