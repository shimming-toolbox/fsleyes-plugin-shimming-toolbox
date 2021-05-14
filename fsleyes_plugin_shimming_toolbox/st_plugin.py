#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shimming Toolbox FSLeyes Plugin

This is an FSLeyes plugin script that integrates ``shimmingtoolbox`` tools into FSLeyes:

- dicom_to_nifti_cli
- mask_cli
- prepare_fieldmap_cli
- realtime_zshim_cli

---------------------------------------------------------------------------------------
Copyright (c) 2021 Polytechnique Montreal <www.neuro.polymtl.ca>
Authors: Alexandre D'Astous, Ainsleigh Hill, Charlotte, Gaspard Cereza, Julien Cohen-Adad
"""

import wx
import os
import tempfile
import logging

import fsleyes.controls.controlpanel as ctrlpanel

from fsleyes_plugin_shimming_toolbox.tabs import DicomToNiftiTab, ShimTab, FieldMapTab, MaskTab


logger = logging.getLogger(__name__)

CURR_DIR = os.getcwd()

DIR = os.path.dirname(__file__)

VERSION = "0.1.1"


class STControlPanel(ctrlpanel.ControlPanel):
    """Class for Shimming Toolbox Control Panel"""

    def __init__(self, ortho, *args, **kwargs):
        """Initialize the control panel.

        Generates the widgets and adds them to the panel. Also sets the initial position of the
        panel to the left.

        Args:
            ortho: This is used to access the ortho ops in order to turn off the X and Y canvas as
                well as the cursor
        """
        ctrlpanel.ControlPanel.__init__(self, ortho, *args, **kwargs)

        my_panel = TabPanel(self)
        sizer_tabs = wx.BoxSizer(wx.VERTICAL)
        sizer_tabs.SetMinSize(400, 300)
        sizer_tabs.Add(my_panel, 0, wx.EXPAND)

        # Set the sizer of the control panel
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sizer_tabs, wx.EXPAND)
        self.SetSizer(sizer)

        # Initialize the variables that are used to track the active image
        self.png_image_name = []
        self.image_dir_path = []
        self.most_recent_watershed_mask_name = None

        # Create a temporary directory that will hold the NIfTI files
        self.st_temp_dir = tempfile.TemporaryDirectory()

        self.verify_version()

    def show_message(self, message, caption="Error"):
        """Show a popup message on the FSLeyes interface.

        Args:
            message (str): message to be displayed
            caption (str): (optional) caption of the message box.
        """
        with wx.MessageDialog(
            self,
            message,
            caption=caption,
            style=wx.OK | wx.CENTRE,
            pos=wx.DefaultPosition,
        ) as msg:
            msg.ShowModal()

    def verify_version(self):
        """Check if the plugin version is the same as the one in the shimming-toolbox directory."""

        st_path = os.path.realpath(__file__)
        plugin_file = os.path.join(st_path, "gui", "st_plugin.py")

        plugin_file_exists = os.path.isfile(plugin_file)

        if not plugin_file_exists:
            return

        # Check the version of the plugin
        with open(plugin_file) as plugin_file_reader:
            plugin_file_lines = plugin_file_reader.readlines()

        plugin_file_lines = [x.strip() for x in plugin_file_lines]
        version_line = f'VERSION = "{VERSION}"'
        plugin_is_up_to_date = True
        version_found = False

        for lines in plugin_file_lines:
            if lines.startswith("VERSION = "):
                version_found = True
                if not lines == version_line:
                    plugin_is_up_to_date = False

        if version_found is False or plugin_is_up_to_date is False:
            message = """
                A more recent version of the ShimmingToolbox plugin was found in your
                ShimmingToolbox installation folder. You will need to replace the current
                FSLeyes plugin with the new one.
                To proceed, go to: File -> Load plugin -> st_plugin.py. Then, restart FSLeyes.
            """
            self.show_message(message, "Warning")
        return

    @staticmethod
    def supportedViews():
        """I am not sure what this method does."""
        from fsleyes.views.orthopanel import OrthoPanel

        return [OrthoPanel]

    @staticmethod
    def defaultLayout():
        """This method makes the control panel appear on the bottom of the FSLeyes window."""
        return {
            "location": wx.BOTTOM,
            "title": "Shimming Toolbox"
        }


class TabPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent=parent)

        nb = wx.Notebook(self)
        tab1 = DicomToNiftiTab(nb)
        tab2 = FieldMapTab(nb)
        tab3 = MaskTab(nb)
        tab4 = ShimTab(nb)

        # Add the windows to tabs and name them.
        nb.AddPage(tab1, tab1.title)
        nb.AddPage(tab2, tab2.title)
        nb.AddPage(tab3, tab3.title)
        nb.AddPage(tab4, tab4.title)

        # Set to the Shim tab
        nb.SetSelection(3)

        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
