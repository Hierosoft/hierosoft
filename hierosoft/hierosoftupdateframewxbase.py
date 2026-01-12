# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.aui

import gettext
_ = gettext.gettext

###########################################################################
## Class HierosoftUpdateFrameWxBase
###########################################################################

class HierosoftUpdateFrameWxBase ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 649,398 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        outerVSizer = wx.BoxSizer( wx.VERTICAL )

        self.m_outerHeaderPanel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        outerVSizer.Add( self.m_outerHeaderPanel, 1, wx.EXPAND |wx.ALL, 5 )

        self.m_notebook = wx.aui.AuiNotebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.aui.AUI_NB_DEFAULT_STYLE )
        self.m_packagesPanel = wx.Panel( self.m_notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        packagesVSizer = wx.BoxSizer( wx.VERTICAL )

        self.m_packagesSplitter = wx.SplitterWindow( self.m_packagesPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_packagesSplitter.Bind( wx.EVT_IDLE, self.m_packagesSplitterOnIdle )

        self.m_packagesListPanel = wx.Panel( self.m_packagesSplitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_packagePanel = wx.Panel( self.m_packagesSplitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_packagesSplitter.SplitVertically( self.m_packagesListPanel, self.m_packagePanel, 0 )
        packagesVSizer.Add( self.m_packagesSplitter, 1, wx.EXPAND, 5 )


        self.m_packagesPanel.SetSizer( packagesVSizer )
        self.m_packagesPanel.Layout()
        packagesVSizer.Fit( self.m_packagesPanel )
        self.m_notebook.AddPage( self.m_packagesPanel, _(u"a page"), False, wx.NullBitmap )

        outerVSizer.Add( self.m_notebook, 9, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( outerVSizer )
        self.Layout()
        self.m_statusBar = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass

    def m_packagesSplitterOnIdle( self, event ):
        self.m_packagesSplitter.SetSashPosition( 0 )
        self.m_packagesSplitter.Unbind( wx.EVT_IDLE )


