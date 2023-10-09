#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import pathlib
import tempfile
import time
import wx

from .test_tabs import get_notebook, set_notebook_page, get_tab, get_all_children
from .. import realYield, run_with_orthopanel
from fsleyes_plugin_shimming_toolbox import __dir_testing__
from fsleyes_plugin_shimming_toolbox.tabs.fieldmap_tab import FieldMapTab


def test_st_plugin_fieldmap_run():
    run_with_orthopanel(_test_st_plugin_fieldmap_run)


def _test_st_plugin_fieldmap_run(view, overlayList, displayCtx):
    """ Makes sure fieldmap tab can be run (Add dummy input and simulate a click) """
    nb_terminal = get_notebook(view)

    # Select the Fieldmap tab
    assert set_notebook_page(nb_terminal, 'Fieldmap')

    # Get the ST tab
    fmap_tab = get_tab(nb_terminal, FieldMapTab)
    assert fmap_tab is not None

    with tempfile.TemporaryDirectory(prefix='st_' + pathlib.Path(__file__).stem) as tmp:
        fname_mag = os.path.join(__dir_testing__, 'ds_b0', 'sub-fieldmap', 'fmap', 'sub-fieldmap_magnitude1.nii.gz')
        fname_phase1 = os.path.join(__dir_testing__, 'ds_b0', 'sub-fieldmap', 'fmap', 'sub-fieldmap_phase1.nii.gz')
        fname_phase2 = os.path.join(__dir_testing__, 'ds_b0', 'sub-fieldmap', 'fmap', 'sub-fieldmap_phase2.nii.gz')
        fname_output = os.path.join(tmp, 'fieldmap.nii.gz')

        # Fill in Fieldmap tab options
        list_widgets = []
        get_all_children(fmap_tab.sizer_run, list_widgets)
        for widget in list_widgets:
            if isinstance(widget, wx.TextCtrl):
                if widget.GetName() == 'no_arg_nechoes':
                    widget.SetValue('2')
                    realYield()
        list_widgets = []
        get_all_children(fmap_tab.sizer_run, list_widgets)
        for widget in list_widgets:
            if isinstance(widget, wx.TextCtrl):
                if widget.GetName() == 'input_phase_1':
                    widget.SetValue(fname_phase1)
                    realYield()
                if widget.GetName() == 'input_phase_2':
                    widget.SetValue(fname_phase2)
                    realYield()
                if widget.GetName() == 'mag':
                    widget.SetValue(fname_mag)
                    realYield()
                if widget.GetName() == 'threshold':
                    widget.SetValue('0.1')
                    realYield()
                if widget.GetName() == 'output':
                    widget.SetValue(fname_output)
                    realYield()

        # Call the function ran when clicking run button
        fmap_tab.run_component.run()

        # Search for files in the overlay for a maximum of 20s
        time_limit = 20  # s
        for i in range(time_limit):
            realYield()
            overlay_file = overlayList.find("fieldmap")
            time.sleep(1)
            if overlay_file:
                break

        # Make sure there is an output in the overlay (that would mean the ST CLI ran)
        assert overlay_file is not None
        assert os.path.exists(fname_output)
