#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import nibabel as nib
import numpy as np
import os
import pathlib
from shimmingtoolbox.masking.shapes import shapes
import tempfile
import time
import wx

from .. import realYield, run_with_orthopanel
from fsleyes_plugin_shimming_toolbox import __dir_testing__
from fsleyes_plugin_shimming_toolbox.tabs.b0shim_tab import B0ShimTab
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


def test_st_plugin_b0shim_run():
    run_with_orthopanel(_test_st_plugin_b0shim_run)


def _test_st_plugin_b0shim_run(view, overlayList, displayCtx):
    """ Makes sure the B0 shim tab runs (Add dummy input and simulate a click) """
    nb_terminal = get_notebook(view)

    # Select the Fieldmap tab
    assert set_notebook_page(nb_terminal, 'B0 Shim')

    # Get the ST tab
    b0shim_tab = get_tab(nb_terminal, B0ShimTab)
    assert b0shim_tab is not None

    with tempfile.TemporaryDirectory(prefix='st_' + pathlib.Path(__file__).stem) as tmp:
        nii_fmap, nii_anat, nii_mask, fm_data, anat_data = _define_inputs(fmap_dim=3)
        fname_fmap = os.path.join(tmp, 'fmap.nii.gz')
        fname_fm_json = os.path.join(tmp, 'fmap.json')
        fname_mask = os.path.join(tmp, 'mask.nii.gz')
        fname_anat = os.path.join(tmp, 'anat.nii.gz')
        fname_anat_json = os.path.join(tmp, 'anat.json')
        _save_inputs(nii_fmap=nii_fmap, fname_fmap=fname_fmap,
                     nii_anat=nii_anat, fname_anat=fname_anat,
                     nii_mask=nii_mask, fname_mask=fname_mask,
                     fm_data=fm_data, fname_fm_json=fname_fm_json,
                     anat_data=anat_data, fname_anat_json=fname_anat_json)
        fname_output = os.path.join(tmp, 'fieldmap.nii.gz')

        # Fill in the B0 shim tab options
        list_widgets = []
        get_all_children(b0shim_tab.sizer_run, list_widgets)
        for widget in list_widgets:
            if isinstance(widget, wx.Choice) and widget.IsShown():
                if widget.GetName() == 'b0shim_algorithms':
                    # Select the proper algorithm
                    assert set_dropdown_selection(widget, 'Dynamic/volume')

        # Select the dropdowns
        list_widgets = []
        get_all_children(b0shim_tab.sizer_run, list_widgets)
        for widget in list_widgets:
            if isinstance(widget, wx.Choice) and widget.IsShown():
                if widget.GetName() == 'optimizer-method':
                    assert set_dropdown_selection(widget, 'Least Squares')
                if widget.GetName() == 'scanner-coil-order':
                    assert set_dropdown_selection(widget, '1')
                # optimizer-criteria, slices, scanner-coil-order, output-file-format-scanner, output-file-format-coil,
                # fatsat, output-value-format

        # Fill in the text boxes
        list_widgets = []
        get_all_children(b0shim_tab.sizer_run, list_widgets)
        for widget in list_widgets:
            if isinstance(widget, wx.TextCtrl):
                if widget.GetName() == 'no_arg_ncoils_dyn':
                    widget.SetValue('0')
                    realYield()
                if widget.GetName() == 'fmap':
                    widget.SetValue(fname_fmap)
                    realYield()
                if widget.GetName() == 'anat':
                    widget.SetValue(fname_anat)
                    realYield()
                if widget.GetName() == 'mask':
                    widget.SetValue(fname_mask)
                    realYield()
                if widget.GetName() == 'mask-dilation-kernel-size':
                    widget.SetValue('5')
                    realYield()
                if widget.GetName() == 'regularization-factor':
                    widget.SetValue('0.1')
                    realYield()
                if widget.GetName() == 'output':
                    widget.SetValue(fname_output)
                    realYield()

        # Call the function ran when clicking run button
        b0shim_tab.run_component_dyn.run()

        # Search for files in the overlay for a maximum of 20s
        time_limit = 20  # s
        for i in range(time_limit):
            realYield()
            overlay_file = overlayList.find("fieldmap_calculated_shim_masked")
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


def set_dropdown_selection(dropdown_widget, selection_name):
    """ Sets the notebook terminal to the page with the given name."""
    for i in range(dropdown_widget.GetCount()):
        if dropdown_widget.GetString(i) == selection_name:
            dropdown_widget.SetSelection(i)
            wx.PostEvent(dropdown_widget.GetEventHandler(), wx.CommandEvent(wx.EVT_CHOICE.typeId, dropdown_widget.GetId()))
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


def _define_inputs(fmap_dim):
    # fname for fmap
    fname_fmap = os.path.join(__dir_testing__, 'ds_b0', 'sub-realtime', 'fmap', 'sub-realtime_fieldmap.nii.gz')
    nii = nib.load(fname_fmap)

    fname_json = os.path.join(__dir_testing__, 'ds_b0', 'sub-realtime', 'fmap', 'sub-realtime_fieldmap.json')

    fm_data = json.load(open(fname_json))

    if fmap_dim == 4:
        nii_fmap = nii
    elif fmap_dim == 3:
        nii_fmap = nib.Nifti1Image(np.mean(nii.get_fdata(), axis=3), nii.affine, header=nii.header)
    elif fmap_dim == 2:
        nii_fmap = nib.Nifti1Image(nii.get_fdata()[..., 0, 0], nii.affine, header=nii.header)
    else:
        raise ValueError("Supported Dimensions are 2, 3 or 4")

    # fname for anat
    fname_anat = os.path.join(__dir_testing__, 'ds_b0', 'sub-realtime', 'anat', 'sub-realtime_unshimmed_e1.nii.gz')

    nii_anat = nib.load(fname_anat)

    fname_anat_json = os.path.join(__dir_testing__, 'ds_b0', 'sub-realtime', 'anat', 'sub-realtime_unshimmed_e1.json')
    anat_data = json.load(open(fname_anat_json))
    anat_data['ScanOptions'] = ['FS']

    anat = nii_anat.get_fdata()

    # Set up mask: Cube
    # static
    nx, ny, nz = anat.shape
    mask = shapes(anat, 'cube',
                  center_dim1=int(nx / 2),
                  center_dim2=int(ny / 2),
                  len_dim1=10, len_dim2=10, len_dim3=nz - 10)

    nii_mask = nib.Nifti1Image(mask.astype(np.uint8), nii_anat.affine)

    return nii_fmap, nii_anat, nii_mask, fm_data, anat_data


def _save_inputs(nii_fmap=None, fname_fmap=None,
                 nii_anat=None, fname_anat=None,
                 nii_mask=None, fname_mask=None,
                 fm_data=None, fname_fm_json=None,
                 anat_data=None, fname_anat_json=None):
    """Save inputs if they are not None, use the respective fnames for the different inputs to save"""
    if nii_fmap is not None:
        # Save the fieldmap
        nib.save(nii_fmap, fname_fmap)

    if fm_data is not None:
        # Save json
        with open(fname_fm_json, 'w', encoding='utf-8') as f:
            json.dump(fm_data, f, indent=4)

    if nii_anat is not None:
        # Save the anat
        nib.save(nii_anat, fname_anat)

    if anat_data is not None:
        # Save json
        with open(fname_anat_json, 'w', encoding='utf-8') as f:
            json.dump(anat_data, f, indent=4)

    if nii_mask is not None:
        # Save the mask
        nib.save(nii_mask, fname_mask)
