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

from .test_tabs import get_notebook, set_notebook_page, get_tab, get_all_children, set_dropdown_selection
from .. import realYield, run_with_orthopanel
from fsleyes_plugin_shimming_toolbox import __dir_testing__
from fsleyes_plugin_shimming_toolbox.tabs.b0shim_tab import B0ShimTab


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
