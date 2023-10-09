#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import pathlib
import tempfile
import time
import wx

from .. import realYield, run_with_orthopanel
from fsleyes_plugin_shimming_toolbox import __dir_testing__
from fsleyes_plugin_shimming_toolbox.tabs.dicom_to_nifti_tab import DicomToNiftiTab
from fsleyes_plugin_shimming_toolbox.tabs.fieldmap_tab import FieldMapTab
from fsleyes_plugin_shimming_toolbox.st_plugin import STControlPanel, NotebookTerminal


def test_st_plugin_loads():
    run_with_orthopanel(_test_st_plugin_loads)


def _test_st_plugin_loads(view, overlayList, displayCtx):
    view.togglePanel(STControlPanel)
    realYield()


def test_st_plugin_tabs_exist():
    run_with_orthopanel(_test_st_plugin_tabs_exist)


def _test_st_plugin_tabs_exist(view, overlayList, displayCtx):
    nb_terminal = get_notebook(view)

    tabs = nb_terminal.GetChildren()
    assert len(tabs) > 0


def test_st_plugin_dcm2niix_run():
    run_with_orthopanel(_test_st_plugin_dcm2niix_run)


def _test_st_plugin_dcm2niix_run(view, overlayList, displayCtx):
    """ Makes sure dicom to nifti tab can be run (Add dummy input and simulate a click) """

    nb_terminal = get_notebook(view)

    # Select the dcm2niix tab
    assert set_notebook_page(nb_terminal, 'Dicom to Nifti')
    # Get the ST tab
    dcm2nifti_tab = get_tab(nb_terminal, DicomToNiftiTab)
    assert dcm2nifti_tab is not None

    with tempfile.TemporaryDirectory(prefix='st_' + pathlib.Path(__file__).stem) as tmp:
        path_input = os.path.join(__dir_testing__, 'dicom_unsorted')

        # Fill in dicom2nifti tab options
        list_widgets = []
        get_all_children(dcm2nifti_tab.sizer_run, list_widgets)
        for widget in list_widgets:
            if isinstance(widget, wx.TextCtrl):
                if widget.GetName() == 'input':
                    widget.SetValue(path_input)
                    realYield()
                if widget.GetName() == 'subject':
                    widget.SetValue('test')
                    realYield()
                if widget.GetName() == 'output':
                    widget.SetValue(tmp)
                    realYield()

        # Call the function ran when clicking run button
        dcm2nifti_tab.run_component.run()

        # Search for files in the overlay for a maximum of 20s
        time_limit = 20  # s
        for i in range(time_limit):
            realYield()
            overlay_file = overlayList.find("sub-test_phase1")
            time.sleep(1)
            if overlay_file:
                break

        # Make sure there is an output in the overlay (that would mean the ST CLI ran)
        assert overlay_file is not None


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


def get_tab(nb_terminal, tab_instance):
    """ Returns the tab instance from the ST notebook."""
    tabs = nb_terminal.GetChildren()
    output_tab = None
    for tab in tabs:
        if isinstance(tab, tab_instance):
            output_tab = tab
            break

    return output_tab


def set_notebook_page(nb_terminal, page_name):
    """ Sets the notebook terminal to the page with the given name."""
    for i in range(nb_terminal.GetPageCount()):
        if nb_terminal.GetPageText(i) == page_name:
            nb_terminal.SetSelection(i)
            realYield()
            return True

    return False


def get_notebook(view):
    """ Returns the notebook terminal from the ST plugin."""

    ctrl = view.togglePanel(STControlPanel)
    realYield()
    children = ctrl.sizer.GetChildren()

    nb_terminal = None
    for child in children:
        tmp = child.GetWindow()
        if isinstance(tmp, NotebookTerminal):
            nb_terminal = tmp
            break

    assert nb_terminal is not None
    return nb_terminal


def get_all_children(item, list_widgets, depth=None):
    """ Returns all children and sub children from an item."""
    if depth is not None:
        depth -= 1

    if depth is not None and depth < 0:
        return

    for sizerItem in item.GetChildren():
        widget = sizerItem.GetWindow()
        if not widget:
            # then it's probably a sizer
            sizer = sizerItem.GetSizer()
            if isinstance(sizer, wx.Sizer):
                get_all_children(sizer, list_widgets, depth=depth)
        else:
            list_widgets.append(widget)
