#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import subprocess
from threading import Thread
import wx

from fsleyes_plugin_shimming_toolbox.events import EVT_RESULT, EVT_LOG, LogEvent, ResultEvent

HOME_DIR = str(Path.home())
PATH_ST_VENV = f"{HOME_DIR}/shimming-toolbox/python/envs/st_venv/bin"


class WorkerThread(Thread):
    def __init__(self, notify_window, cmd):
        Thread.__init__(self)
        self._notify_window = notify_window
        self.cmd = cmd
        self.start()

    def run(self):

        try:
            env = os.environ.copy()
            # It seems to default to the Python executalble instead of the Shebang, removing it fixes it
            env["PYTHONEXECUTABLE"] = ""
            env["PATH"] = PATH_ST_VENV + ":" + env["PATH"]
            
            # Run command using realtime output
            process = subprocess.Popen(self.cmd.split(' '),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       text=True,
                                       env=env)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    wx.PostEvent(self._notify_window, LogEvent(output.strip()))

            rc = process.poll()
            wx.PostEvent(self._notify_window, ResultEvent(rc))
        except Exception as err:
            # Send the error if there was one
            wx.PostEvent(self._notify_window, ResultEvent(err))
