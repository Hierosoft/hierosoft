# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys

import wx

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(MODULE_DIR)
    sys.path.insert(0, REPO_DIR)

from hierosoft.hierosoftupdateframewxbase import HierosoftUpdateFrameWxBase
from hierosoft.moreweb.hierosoftupdate import HierosoftUpdate


class HierosoftUpdateFrameWx(HierosoftUpdateFrameWxBase, HierosoftUpdate):
    def __init__(self, *args, **kwargs):
        HierosoftUpdateFrameWxBase.__init__(self, *args, **kwargs)
        # HierosoftUpdate.__init__(self, *args, **kwargs)
        # Assuming 'self.m_auinotebook1' is the name from wxFormBuilder
        # Hide tab (only works for AUINotebook):
        self.m_notebook.SetSelection(0)  # Select the page you want displayed (0-based index)
        self.m_notebook.SetTabCtrlHeight(0)  # Hide the tab bar
        self.Layout()  # Refresh the layout if needed


def main():
    app = wx.App(False)  # Create the application (False to not redirect stdout/stderr)
    frame = HierosoftUpdateFrameWx(None)  # Instantiate the frame with no parent
    frame.Show(True)  # Show the frame
    app.MainLoop()  # Start the main event loop
    return 0


if __name__ == "__main__":
    sys.exit(main())