#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx

EVT_LOG_ID = wx.NewId()
EVT_RESULT_ID = wx.NewId()


def EVT_RESULT(win, func):
    """Define Result Event."""
    win.panel.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


def EVT_LOG(win, func):
    """Define Result Event."""
    win.panel.Connect(-1, -1, EVT_LOG_ID, func)


class LogEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_LOG_ID)
        self.data = data
