#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shimming Toolbox FSLeyes Plugin

This is an FSLeyes plugin that integrates the following ``shimmingtoolbox`` tools into FSLeyes' GUI:

- st_dicom_to_nifti
- st_mask
- st_prepare_fieldmap
- st_b0shim
- st_b1shim

---------------------------------------------------------------------------------------
Copyright (c) 2021 Polytechnique Montreal <www.neuro.polymtl.ca>
Authors: Alexandre D'Astous, Ainsleigh Hill, Gaspard Cereza, Julien Cohen-Adad
"""

import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.actions.loadoverlay as loadoverlay
import fsleyes.views.canvaspanel as canvaspanel
import glob
import imageio
import logging
import nibabel as nib
import numpy as np
import os
from pathlib import Path
import webbrowser
import wx

from fsleyes_plugin_shimming_toolbox import __dir_st_plugin__
from fsleyes_plugin_shimming_toolbox.components.dropdown import DropdownComponent
from fsleyes_plugin_shimming_toolbox.components.run import RunComponent
from fsleyes_plugin_shimming_toolbox.components.input import InputComponent
from shimmingtoolbox.cli.b0shim import dynamic as dynamic_cli
from shimmingtoolbox.cli.b0shim import realtime_dynamic as realtime_cli
from shimmingtoolbox.cli.b0shim import max_intensity as max_intensity_cli
from shimmingtoolbox.cli.b1shim import b1shim_cli
from shimmingtoolbox.cli.dicom_to_nifti import dicom_to_nifti_cli
from shimmingtoolbox.cli.mask import box, rect, threshold, sphere
from shimmingtoolbox.cli.prepare_fieldmap import prepare_fieldmap_cli

logger = logging.getLogger(__name__)

HOME_DIR = str(Path.home())
CURR_DIR = os.getcwd()
ST_DIR = f"{HOME_DIR}/shimming-toolbox"

VERSION = "0.1.1"

# Load icon resources
rtd_logo = wx.Bitmap(os.path.join(__dir_st_plugin__, 'img', 'RTD.png'), wx.BITMAP_TYPE_PNG)
# Load ShimmingToolbox logo saved as a png image, rescale it, and return it as a wx.Bitmap image.
st_logo = wx.Image(os.path.join(__dir_st_plugin__, 'img', 'shimming_toolbox_logo.png'), wx.BITMAP_TYPE_PNG)
st_logo.Rescale(int(st_logo.GetWidth() * 0.2), int(st_logo.GetHeight() * 0.2), wx.IMAGE_QUALITY_HIGH)
st_logo = st_logo.ConvertToBitmap()


# We need to create a ctrlpanel.ControlPanel instance so that it can be recognized as a plugin by FSLeyes
# Class hierarchy: wx.Panel > fslpanel.FSLeyesPanel > ctrlpanel.ControlPanel
class STControlPanel(ctrlpanel.ControlPanel):
    """Class for Shimming Toolbox Control Panel"""

    # The CanvasPanel view is used for most FSLeyes plugins so we decided to stick to it
    @staticmethod
    def supportedViews():
        return [canvaspanel.CanvasPanel]

    @staticmethod
    def defaultLayout():
        """This method makes the control panel appear on the top of the FSLeyes window."""
        return {"location": wx.TOP, "title": "Shimming Toolbox"}

    def __init__(self, parent, overlayList, displayCtx, ctrlPanel):
        """Initialize the control panel.

        Generates the widgets and adds them to the panel.

        """
        super().__init__(parent, overlayList, displayCtx, ctrlPanel)
        # Create a notebook with a terminal to navigate between the different functions.
        nb = NotebookTerminal(self)

        # Create the different tabs. Use 'select' to choose the default tab displayed at startup
        tab1 = DicomToNiftiTab(nb)
        tab2 = FieldMapTab(nb)
        tab3 = MaskTab(nb)
        tab4 = B0ShimTab(nb)
        tab5 = B1ShimTab(nb)
        nb.AddPage(tab1, tab1.title)
        nb.AddPage(tab2, tab2.title)
        nb.AddPage(tab3, tab3.title)
        nb.AddPage(tab4, tab4.title, select=True)
        nb.AddPage(tab5, tab5.title)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(nb, 2, wx.EXPAND)
        self.sizer.Add(nb.terminal_component.sizer, 1, wx.EXPAND)
        self.sizer.AddSpacer(5)
        self.sizer.SetMinSize((600, 400))
        self.SetSizer(self.sizer)


class NotebookTerminal(wx.Notebook):
    """Notebook class with an extra terminal attribute"""
    def __init__(self, parent):
        super().__init__(parent)
        self.terminal_component = Terminal(parent)


class Tab(wx.ScrolledWindow):
    def __init__(self, parent, title, description):
        super().__init__(parent)
        self.title = title
        self.sizer_info = InfoSection(self, description).sizer
        self.terminal_component = parent.terminal_component
        self.SetScrollbars(1, 4, 1, 1)

    def create_sizer(self):
        """Create the parent sizer for the tab.

        Tab is divided into 2 main sizers:
            sizer_info | sizer_run
        """
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_info, 0)
        sizer.AddSpacer(20)
        sizer.Add(self.sizer_run, 2)
        return sizer

    def create_sizer_run(self):
        """Create the run sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(400, 300)
        sizer.AddSpacer(10)
        return sizer

    def create_empty_component(self):
        component = InputComponent(panel=self, input_text_box_metadata=[])
        return component


class Terminal:
    """Create the terminal where messages are logged to the user."""
    def __init__(self, panel):
        self.panel = panel
        self.terminal = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.terminal.SetDefaultStyle(wx.TextAttr(wx.WHITE, wx.BLACK))
        self.terminal.SetBackgroundColour(wx.BLACK)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self.terminal, 1, wx.EXPAND)
        self.sizer.AddSpacer(5)

    def log_to_terminal(self, msg, level=None):
        if level is None:
            self.terminal.AppendText(f"{msg}\n")
        else:
            self.terminal.AppendText(f"{level}: {msg}\n")


class InfoSection:
    def __init__(self, panel, description):
        self.panel = panel
        self.description = description
        self.sizer = self.create_sizer()

    def create_sizer(self):
        """Create the left sizer containing generic Shimming Toolbox information."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        logo = wx.StaticBitmap(parent=self.panel, id=-1, bitmap=st_logo, pos=wx.DefaultPosition)
        width = logo.Size[0]
        sizer.Add(logo, flag=wx.SHAPED, proportion=1)
        sizer.AddSpacer(10)

        # Create a "Documentation" button that redirects towards https://shimming-toolbox.org/en/latest/
        button_documentation = wx.Button(self.panel, label="Documentation")
        button_documentation.Bind(wx.EVT_BUTTON, self.open_documentation_url)
        button_documentation.SetBitmap(rtd_logo)
        sizer.Add(button_documentation, flag=wx.EXPAND)
        sizer.AddSpacer(10)

        # Add a short description of what the current tab does
        description_text = wx.StaticText(self.panel, id=-1, label=self.description)
        description_text.Wrap(width)
        sizer.Add(description_text)
        return sizer

    def open_documentation_url(self, event):
        """Redirect ``button_documentation`` to the ``shimming-toolbox`` page."""
        webbrowser.open('https://shimming-toolbox.org/en/latest/')


class B0ShimTab(Tab):
    def __init__(self, parent, title="B0 Shim"):

        description = "Perform B0 shimming.\n\n" \
                      "Select the shimming algorithm from the dropdown list."
        super().__init__(parent, title, description)

        self.sizer_run = self.create_sizer_run()
        self.positions = {}
        self.dropdown_metadata = [
            {
                "name": "Dynamic",
                "sizer_function": self.create_sizer_dynamic_shim
            },
            {
                "name": "Realtime Dynamic",
                "sizer_function": self.create_sizer_realtime_shim
            },
            {
                "name": "Maximum Intensity",
                "sizer_function": self.create_sizer_max_intensity
            },
        ]
        self.dropdown_choices = [item["name"] for item in self.dropdown_metadata]

        # Dyn + rt shim
        self.n_coils_rt = 0
        self.n_coils_dyn = 0
        self.component_coils_dyn = None
        self.component_coils_rt = None

        self.create_choice_box()

        self.create_dropdown_sizers()
        self.parent_sizer = self.create_sizer()
        self.SetSizer(self.parent_sizer)

        # Run on choice to select the default choice from the choice box widget
        self.on_choice(None)

    def create_dropdown_sizers(self):
        for dropdown_dict in self.dropdown_metadata:
            sizer = dropdown_dict["sizer_function"]()
            self.sizer_run.Add(sizer, 0, wx.EXPAND)
            self.positions[dropdown_dict["name"]] = self.sizer_run.GetItemCount() - 1

    def on_choice(self, event):
        # Get the selection from the choice box widget
        if self.choice_box.GetSelection() < 0:
            selection = self.choice_box.GetString(0)
            self.choice_box.SetSelection(0)
        else:
            selection = self.choice_box.GetString(self.choice_box.GetSelection())

        # Unshow everything then show the correct item according to the choice box
        self.unshow_choice_box_sizers()
        if selection in self.positions.keys():
            run_component_sizer_item = self.sizer_run.GetItem(self.positions[selection])
            run_component_sizer_item.Show(True)

            # When doing Show(True), we show everything in the sizer, we need to call the dropdowns that can contain
            # items to show the appropriate things according to their current choice.
            if selection == 'Dynamic':
                self.dropdown_slice_dyn.on_choice(None)
                self.dropdown_coil_format_dyn.on_choice(None)
                self.dropdown_scanner_order_dyn.on_choice(None)
                self.dropdown_opt_dyn.on_choice(None)
            elif selection == 'Realtime Dynamic':
                self.dropdown_slice_rt.on_choice(None)
                self.dropdown_coil_format_rt.on_choice(None)
                self.dropdown_scanner_order_rt.on_choice(None)
                self.dropdown_opt_rt.on_choice(None)
        else:
            pass

        # Update the window
        self.SetVirtualSize(self.sizer_run.GetMinSize())
        self.Layout()

    def unshow_choice_box_sizers(self):
        """Set the Show variable to false for all sizers of the choice box widget"""
        for position in self.positions.values():
            sizer_item = self.sizer_run.GetItem(position)
            sizer_item.Show(False)

    def create_choice_box(self):
        self.choice_box = wx.Choice(self, choices=self.dropdown_choices)
        self.choice_box.Bind(wx.EVT_CHOICE, self.on_choice)
        self.sizer_run.Add(self.choice_box)
        self.sizer_run.AddSpacer(10)

    def create_sizer_dynamic_shim(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "output_dynamic_shim")

        # no_arg is used here since a --coil option must be used for each of the coils (defined add_input_coil_boxes)
        input_text_box_metadata_coil = [
            {
                "button_label": "Number of Custom Coils",
                "button_function": "add_input_coil_boxes_dyn",
                "name": "no_arg",
                "info_text": "Number of phase NIfTI files to be used. Must be an integer > 0.",
            }
        ]
        self.component_coils_dyn = InputComponent(self, input_text_box_metadata_coil)

        input_text_box_metadata_inputs = [
            {
                "button_label": "Input Fieldmap",
                "name": "fmap",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Anat",
                "name": "anat",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Mask",
                "name": "mask",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Mask Dilation Kernel Size",
                "name": "mask-dilation-kernel-size",
                "default_text": "3",
            }
        ]

        component_inputs = InputComponent(self, input_text_box_metadata_inputs, cli=dynamic_cli)

        input_text_box_metadata_slice = [
            {
                "button_label": "Slice Factor",
                "name": "slice-factor",
                "default_text": "1",
            },
        ]
        component_slice_int = InputComponent(self, input_text_box_metadata_slice, cli=dynamic_cli)
        component_slice_seq = InputComponent(self, input_text_box_metadata_slice, cli=dynamic_cli)

        output_metadata = [
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]
        component_output = InputComponent(self, output_metadata, cli=dynamic_cli)
        
        input_text_box_metadata_scanner = [
            {
                "button_label": "Scanner constraints",
                "button_function": "select_file",
                "name": "scanner-coil-constraints",
                "default_text": f"{os.path.join(ST_DIR, 'coil_config.json')}",
            },
        ]
        component_scanner1 = InputComponent(self, input_text_box_metadata_scanner, cli=dynamic_cli)
        component_scanner2 = InputComponent(self, input_text_box_metadata_scanner, cli=dynamic_cli)
        component_scanner3 = InputComponent(self, input_text_box_metadata_scanner, cli=dynamic_cli)
        
        dropdown_scanner_format_metadata = [
            {
                "label": "Slicewise per Channel",
                "option_value": "slicewise-ch"
            },
            {
                "label": "Slicewise per Coil",
                "option_value": "slicewise-coil"
            },
            {
                "label": "Chronological per Channel",
                "option_value": "chronological-ch"
            },
            {
                "label": "Chronological per Coil",
                "option_value": "chronological-coil"
            },
            {
                "label": "Gradient per Channel",
                "option_value": "gradient"
            },
        ]

        dropdown_scanner_format1 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_format_metadata,
            option_name='output-file-format-scanner',
            label="Scanner Output Format",
            cli=dynamic_cli
        )
        
        dropdown_scanner_format2 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_format_metadata,
            option_name='output-file-format-scanner',
            label="Scanner Output Format",
            cli=dynamic_cli
        )
        
        dropdown_scanner_format3 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_format_metadata,
            option_name='output-file-format-scanner',
            label="Scanner Output Format",
            cli=dynamic_cli
        )
        
        dropdown_scanner_order_metadata = [
            {
                "label": "-1",
                "option_value": "-1"
            },
            {
                "label": "0",
                "option_value": "0"
            },
            {
                "label": "1",
                "option_value": "1"
            },
            {
                "label": "2",
                "option_value": "2"
            }
        ]

        self.dropdown_scanner_order_dyn = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_order_metadata,
            label="Scanner Order",
            option_name='scanner-coil-order',
            list_components=[self.create_empty_component(),
                             dropdown_scanner_format1, component_scanner1,
                             dropdown_scanner_format2, component_scanner2,
                             dropdown_scanner_format3, component_scanner3],
            component_to_dropdown_choice=[0, 1, 1, 2, 2, 3, 3],
            cli=dynamic_cli
        )

        dropdown_scanner_format1.add_dropdown_parent(self.dropdown_scanner_order_dyn)
        dropdown_scanner_format2.add_dropdown_parent(self.dropdown_scanner_order_dyn)
        dropdown_scanner_format3.add_dropdown_parent(self.dropdown_scanner_order_dyn)

        dropdown_ovf_metadata = [
            {
                "label": "delta",
                "option_value": "delta"
            },
            {
                "label": "absolute",
                "option_value": "absolute"
            }
        ]

        dropdown_ovf = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_ovf_metadata,
            label="Output Value Format",
            option_name='output-value-format',
            cli=dynamic_cli
        )

        reg_factor_metadata = [
            {
                "button_label": "Regularization factor",
                "default_text": '0.0',
                "name": 'regularization-factor',
            }
        ]
        component_reg_factor = InputComponent(self, reg_factor_metadata, cli=dynamic_cli)

        criteria_dropdown_metadata = [
            {
                "label": "Mean Squared Error",
                "option_value": "mse",
            },
            {
                "label": "Mean Absolute Error",
                "option_value": "mae",
            },
        ]
        
        dropdown_crit = DropdownComponent(
            panel=self,
            dropdown_metadata=criteria_dropdown_metadata,
            label="Optimizer Criteria",
            option_name='optimizer-criteria',
            cli=dynamic_cli
        )
        
        dropdown_opt_metadata = [
            {
                "label": "Least Squares",
                "option_value": "least_squares"
            },
            {
                "label": "Pseudo Inverse",
                "option_value": "pseudo_inverse"
            },
        ]

        self.dropdown_opt_dyn = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_opt_metadata,
            label="Optimizer",
            option_name='optimizer-method',
            list_components=[dropdown_crit, component_reg_factor, self.create_empty_component()],
            component_to_dropdown_choice=[0, 0, 1],
            cli=dynamic_cli
        )

        dropdown_crit.add_dropdown_parent(self.dropdown_opt_dyn)

        dropdown_slice_metadata = [
            {
                "label": "Auto detect",
                "option_value": "auto"
            },
            {
                "label": "Sequential",
                "option_value": "sequential"
            },
            {
                "label": "Interleaved",
                "option_value": "interleaved"
            },
            {
                "label": "Volume",
                "option_value": "volume"
            },
        ]

        self.dropdown_slice_dyn = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_slice_metadata,
            label="Slice Ordering",
            cli=dynamic_cli,
            option_name='slices',
            list_components=[self.create_empty_component(),
                             component_slice_seq,
                             component_slice_int,
                             self.create_empty_component()]
        )

        dropdown_coil_format_metadata = [
            {
                "label": "Slicewise per Channel",
                "option_value": "slicewise-ch"
            },
            {
                "label": "Slicewise per Coil",
                "option_value": "slicewise-coil"
            },
            {
                "label": "Chronological per Channel",
                "option_value": "chronological-ch"
            },
            {
                "label": "Chronological per Coil",
                "option_value": "chronological-coil"
            },
        ]

        dropdown_fatsat_metadata = [
            {
                "label": "Auto detect",
                "option_value": "auto"
            },
            {
                "label": "Yes",
                "option_value": "yes"
            },
            {
                "label": "No",
                "option_value": "no"
            },
        ]

        dropdown_fatsat1 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_fatsat_metadata,
            option_name='fatsat',
            label="Fat Saturation",
            cli=dynamic_cli
        )

        dropdown_fatsat2 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_fatsat_metadata,
            option_name='fatsat',
            label="Fat Saturation",
            cli=dynamic_cli
        )

        self.dropdown_coil_format_dyn = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_coil_format_metadata,
            label="Custom Coil Output Format",
            option_name='output-file-format-coil',
            cli=dynamic_cli,
            list_components=[self.create_empty_component(),
                             self.create_empty_component(),
                             dropdown_fatsat1,
                             dropdown_fatsat2]
        )

        dropdown_fatsat1.add_dropdown_parent(self.dropdown_coil_format_dyn)
        dropdown_fatsat2.add_dropdown_parent(self.dropdown_coil_format_dyn)

        run_component = RunComponent(
            panel=self,
            list_components=[self.component_coils_dyn, component_inputs, self.dropdown_opt_dyn, self.dropdown_slice_dyn,
                             self.dropdown_scanner_order_dyn,
                             self.dropdown_coil_format_dyn, dropdown_ovf, component_output],
            st_function="st_b0shim dynamic",
            output_paths=["fieldmap_calculated_shim_masked.nii.gz",
                          "fieldmap_calculated_shim.nii.gz"]
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_realtime_shim(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "output_realtime_shim")

        # no_arg is used here since a --coil option must be used for each of the coils (defined add_input_coil_boxes)
        input_text_box_metadata_coil = [
            {
                "button_label": "Number of Custom Coils",
                "button_function": "add_input_coil_boxes_rt",
                "name": "no_arg",
                "info_text": "Number of phase NIfTI files to be used. Must be an integer > 0.",
            }
        ]
        self.component_coils_rt = InputComponent(self, input_text_box_metadata_coil, cli=realtime_cli)

        input_text_box_metadata_inputs = [
            {
                "button_label": "Input Fieldmap",
                "name": "fmap",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Anat",
                "name": "anat",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Respiratory Trace",
                "name": "resp",
                "button_function": "select_file",
                "required": True
            },
            {
                "button_label": "Input Mask Static",
                "name": "mask-static",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Input Mask Realtime",
                "name": "mask-riro",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Mask Dilation Kernel Size",
                "name": "mask-dilation-kernel-size",
                "default_text": "3",
            }
        ]

        component_inputs = InputComponent(self, input_text_box_metadata_inputs, cli=realtime_cli)

        input_text_box_metadata_scanner = [
            {
                "button_label": "Scanner constraints",
                "button_function": "select_file",
                "name": "scanner-coil-constraints",
                "default_text": f"{os.path.join(ST_DIR, 'coil_config.json')}",
            },
        ]
        component_scanner1 = InputComponent(self, input_text_box_metadata_scanner, cli=realtime_cli)
        component_scanner2 = InputComponent(self, input_text_box_metadata_scanner, cli=realtime_cli)
        component_scanner3 = InputComponent(self, input_text_box_metadata_scanner, cli=realtime_cli)

        input_text_box_metadata_slice = [
            {
                "button_label": "Slice Factor",
                "name": "slice-factor",
                "default_text": "1",
            },
        ]
        component_slice_int = InputComponent(self, input_text_box_metadata_slice, cli=realtime_cli)
        component_slice_seq = InputComponent(self, input_text_box_metadata_slice, cli=realtime_cli)

        output_metadata = [
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]
        component_output = InputComponent(self, output_metadata, cli=realtime_cli)

        dropdown_scanner_format_metadata = [
            {
                "label": "Slicewise per Channel",
                "option_value": "slicewise-ch"
            },
            {
                "label": "Chronological per Channel",
                "option_value": "chronological-ch"
            },
            {
                "label": "Gradient per Channel",
                "option_value": "gradient"
            },
        ]

        dropdown_scanner_format1 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_format_metadata,
            label="Scanner Output Format",
            option_name = 'output-file-format-scanner',
            cli=realtime_cli
        )

        dropdown_scanner_format2 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_format_metadata,
            label="Scanner Output Format",
            option_name = 'output-file-format-scanner',
            cli=realtime_cli
        )

        dropdown_scanner_format3 = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_format_metadata,
            label="Scanner Output Format",
            option_name = 'output-file-format-scanner',
            cli=realtime_cli
        )

        dropdown_scanner_order_metadata = [
            {
                "label": "-1",
                "option_value": "-1"
            },
            {
                "label": "0",
                "option_value": "0"
            },
            {
                "label": "1",
                "option_value": "1"
            },
            {
                "label": "2",
                "option_value": "2"
            }
        ]

        self.dropdown_scanner_order_rt = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_scanner_order_metadata,
            label="Scanner Order",
            option_name = 'scanner-coil-order',
            list_components=[self.create_empty_component(),
                             dropdown_scanner_format1, component_scanner1,
                             dropdown_scanner_format2, component_scanner2,
                             dropdown_scanner_format3, component_scanner3],
            component_to_dropdown_choice=[0, 1, 1, 2, 2, 3, 3],
            cli=realtime_cli
        )

        dropdown_scanner_format1.add_dropdown_parent(self.dropdown_scanner_order_rt)
        dropdown_scanner_format2.add_dropdown_parent(self.dropdown_scanner_order_rt)
        dropdown_scanner_format3.add_dropdown_parent(self.dropdown_scanner_order_rt)

        dropdown_ovf_metadata = [
            {
                "label": "delta",
                "option_value": "delta"
            },
            {
                "label": "absolute",
                "option_value": "absolute"
            }
        ]

        dropdown_ovf = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_ovf_metadata,
            label="Output Value Format",
            option_name = 'output-value-format',
            cli=realtime_cli
        )

        reg_factor_metadata = [
            {
                "button_label": "Regularization factor",
                "default_text": '0.0',
                "name": 'regularization-factor',
            }
        ]
        component_reg_factor = InputComponent(self, reg_factor_metadata, cli=dynamic_cli)

        criteria_dropdown_metadata = [
            {
                "label": "Mean Squared Error",
                "option_value": "mse",
            },
            {
                "label": "Mean Absolute Error",
                "option_value": "mae",
            },
        ]

        dropdown_crit = DropdownComponent(
            panel=self,
            dropdown_metadata=criteria_dropdown_metadata,
            label="Optimizer Criteria",
            option_name='optimizer-criteria',
            cli=dynamic_cli
        )

        dropdown_opt_metadata = [
            {
                "label": "Least Squares",
                "option_value": "least_squares"
            },
            {
                "label": "Pseudo Inverse",
                "option_value": "pseudo_inverse"
            },
        ]

        self.dropdown_opt_rt = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_opt_metadata,
            label="Optimizer",
            option_name = 'optimizer-method',
            list_components= [dropdown_crit, component_reg_factor, self.create_empty_component()],
            component_to_dropdown_choice=[0, 0, 1],
            cli=realtime_cli
        )

        dropdown_crit.add_dropdown_parent(self.dropdown_opt_rt)

        dropdown_slice_metadata = [
            {
                "label": "Auto detect",
                "option_value": "auto"
            },
            {
                "label": "Sequential",
                "option_value": "sequential"
            },
            {
                "label": "Interleaved",
                "option_value": "interleaved"
            },
            {
                "label": "Volume",
                "option_value": "volume"
            },
        ]

        self.dropdown_slice_rt = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_slice_metadata,
            label="Slice Ordering",
            option_name = 'slices',
            list_components=[self.create_empty_component(),
                             component_slice_seq,
                             component_slice_int,
                             self.create_empty_component()],
            cli=realtime_cli
        )

        dropdown_fatsat_metadata = [
            {
                "label": "Auto detect",
                "option_value": "auto"
            },
            {
                "label": "Yes",
                "option_value": "yes"
            },
            {
                "label": "No",
                "option_value": "no"
            },
        ]

        dropdown_fatsat = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_fatsat_metadata,
            label="Fat Saturation",
            option_name = 'fatsat',
            cli=realtime_cli
        )

        dropdown_coil_format_metadata = [
            {
                "label": "Slicewise per Channel",
                "option_value": "slicewise-ch"
            },
            {
                "label": "Chronological per Channel",
                "option_value": "chronological-ch"
            }
        ]

        self.dropdown_coil_format_rt = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_coil_format_metadata,
            label="Custom Coil Output Format",
            option_name = 'output-file-format-coil',
            cli=realtime_cli,
            list_components=[self.create_empty_component(),
                             dropdown_fatsat]
        )

        dropdown_fatsat.add_dropdown_parent(self.dropdown_coil_format_rt)

        run_component = RunComponent(
            panel=self,
            list_components=[self.component_coils_rt, component_inputs, self.dropdown_opt_rt, self.dropdown_slice_rt,
                             self.dropdown_scanner_order_rt,
                             self.dropdown_coil_format_rt, dropdown_ovf, component_output],
            st_function="st_b0shim realtime-dynamic",
            # TODO: output paths
            output_paths=[]
        )
        sizer = run_component.sizer
        return sizer
    
    def create_sizer_max_intensity(self, metadata=None):
        fname_output = os.path.join(CURR_DIR, "output_maximum_intensity", "shim_index.txt")

        inputs_metadata = [
            {
                "button_label": "Input File",
                "button_function": "select_from_overlay",
                "required": True,
                "name": "input",
            },
            {
                "button_label": "Input Mask",
                "name": "mask",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Output File",
                "default_text": fname_output,
                "name": "output",
            }
        ]
        component_inputs = InputComponent(self, inputs_metadata, cli=max_intensity_cli)
        
        run_component = RunComponent(
            panel=self,
            list_components=[component_inputs],
            st_function="st_b0shim max-intensity",
            output_paths=[]
        )
        sizer = run_component.sizer
        return sizer
    
    
class B1ShimTab(Tab):
    def __init__(self, parent, title=r"B1+ Shim"):

        description = "Perform B1+ shimming.\n\n" \
                      "Select the shimming algorithm from the dropdown list."
        super().__init__(parent, title, description)

        self.sizer_run = self.create_sizer_run()
        self.positions = {}
        self.dropdown_metadata = [
            {
                "name": "CV reduction",
                "sizer_function": self.create_sizer_cv
            },
            {
                "name": "Target",
                "sizer_function": self.create_sizer_target
            },
            {
                "name": "SAR efficiency",
                "sizer_function": self.create_sizer_sar_eff
            },
            {
                "name": "Phase-only",
                "sizer_function": self.create_sizer_phase_only
            }
        ]
        self.dropdown_choices = [item["name"] for item in self.dropdown_metadata]

        self.create_choice_box()

        self.create_dropdown_sizers()
        self.parent_sizer = self.create_sizer()
        self.SetSizer(self.parent_sizer)

        # Run on choice to select the default choice from the choice box widget
        self.on_choice(None)

    def create_dropdown_sizers(self):
        for dropdown_dict in self.dropdown_metadata:
            sizer = dropdown_dict["sizer_function"]()
            self.sizer_run.Add(sizer, 0, wx.EXPAND)
            self.positions[dropdown_dict["name"]] = self.sizer_run.GetItemCount() - 1

    def on_choice(self, event):
        # Get the selection from the choice box widget
        if self.choice_box.GetSelection() < 0:
            selection = self.choice_box.GetString(0)
            self.choice_box.SetSelection(0)
        else:
            selection = self.choice_box.GetString(self.choice_box.GetSelection())

        # Unshow everything then show the correct item according to the choice box
        self.unshow_choice_box_sizers()
        if selection in self.positions.keys():
            sizer_item = self.sizer_run.GetItem(self.positions[selection])
            sizer_item.Show(True)
        else:
            pass

        # Update the window
        self.SetVirtualSize(self.sizer_run.GetMinSize())
        self.Layout()

    def unshow_choice_box_sizers(self):
        """Set the Show variable to false for all sizers of the choice box widget"""
        for position in self.positions.values():
            sizer_item = self.sizer_run.GetItem(position)
            sizer_item.Show(False)

    def create_choice_box(self):
        self.choice_box = wx.Choice(self, choices=self.dropdown_choices)
        self.choice_box.Bind(wx.EVT_CHOICE, self.on_choice)
        self.sizer_run.Add(self.choice_box)
        self.sizer_run.AddSpacer(10)

    def create_sizer_cv(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "b1_shim_output")
        input_text_box_metadata = [
            {
                "button_label": "Input B1+ map",
                "name": "b1",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Mask",
                "name": "mask",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Input VOP file",
                "name": "vop",
                "button_function": "select_file",
            },
            {
                "button_label": "SAR factor",
                "name": "sar_factor",
                "default_text": "1.5",
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]

        component = InputComponent(self, input_text_box_metadata, cli=b1shim_cli)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_b1shim --algo 1",
            output_paths=['TB1map_shimmed.nii.gz']
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_target(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "b1_shim_output")
        input_text_box_metadata = [
            {
                "button_label": "Input B1+ map",
                "name": "b1",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Mask",
                "name": "mask",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Target value (nT/V)",
                "name": "target",
                "default_text": "20",
                "required": True
            },
            {
                "button_label": "Input VOP file",
                "name": "vop",
                "button_function": "select_file",
            },
            {
                "button_label": "SAR factor",
                "name": "sar_factor",
                "default_text": "1.5",
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]

        component = InputComponent(self, input_text_box_metadata, cli=b1shim_cli)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_b1shim --algo 2",
            output_paths=['TB1map_shimmed.nii.gz']
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_sar_eff(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "b1_shim_output")
        input_text_box_metadata = [
            {
                "button_label": "Input B1+ map",
                "name": "b1",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Mask",
                "name": "mask",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Input VOP file",
                "name": "vop",
                "button_function": "select_file",
                "required": True
            },
            {
                "button_label": "SAR factor",
                "name": "sar_factor",
                "default_text": "1.5",
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]

        component = InputComponent(self, input_text_box_metadata, cli=b1shim_cli)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_b1shim --algo 3",
            output_paths=['TB1map_shimmed.nii.gz']
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_phase_only(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "b1_shim_output")
        input_text_box_metadata = [
            {
                "button_label": "Input B1+ maps",
                "name": "b1",
                "button_function": "select_from_overlay",
                "required": True
            },
            {
                "button_label": "Input Mask",
                "name": "mask",
                "button_function": "select_from_overlay",
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]
        component = InputComponent(self, input_text_box_metadata, cli=b1shim_cli)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_b1shim --algo 4",
            output_paths=['TB1map_shimmed.nii.gz']
        )
        sizer = run_component.sizer
        return sizer


class FieldMapTab(Tab):
    def __init__(self, parent, title="Fieldmap"):
        description = "Create a B0 fieldmap.\n\n" \
                      "Enter the Number of Echoes then press the `Number of Echoes` button.\n\n" \
                      "Select the unwrapper from the dropdown list."
        super().__init__(parent, title, description)

        self.sizer_run = self.create_sizer_run()
        self.n_echoes = 0
        sizer = self.create_fieldmap_sizer()
        self.sizer_run.Add(sizer, 0, wx.EXPAND)

        self.parent_sizer = self.create_sizer()
        self.SetSizer(self.parent_sizer)

    def create_fieldmap_sizer(self):

        input_text_box_metadata_input = [
            {
                "button_label": "Number of Echoes",
                "button_function": "add_input_phase_boxes",
                "name": "no_arg",
                "info_text": "Number of phase NIfTI files to be used. Must be an integer > 0.",
                "required": True
            }
        ]
        self.component_input = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_input
        )

        dropdown_metadata_unwrapper = [
            {
                "label": "prelude",
                "option_value": "prelude"
            }
        ]
        self.dropdown_unwrapper = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_metadata_unwrapper,
            label="Unwrapper",
            option_name = 'unwrapper',
            cli=prepare_fieldmap_cli
        )

        mask_metadata = [
            {
                "button_label": "Input Mask",
                "button_function": "select_from_overlay",
                "name": "mask",
            }
        ]
        self.component_mask = InputComponent(
            panel=self,
            input_text_box_metadata=mask_metadata,
            cli=prepare_fieldmap_cli
        )

        threshold_metadata = [
            {
                "button_label": "Threshold",
                "name": "threshold",
            },
            {
                "button_label": "Output Calculated Mask",
                "name": "savemask",
                "load_in_overlay": True
            }
        ]
        self.component_threshold = InputComponent(
            panel=self,
            input_text_box_metadata=threshold_metadata,
            cli=prepare_fieldmap_cli
        )

        dropdown_mask_threshold = [
            {
                "label": "mask",
                "option_value": ""
            },
            {
                "label": "threshold",
                "option_value": ""
            },
        ]
        self.dropdown_mask_threshold = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_mask_threshold,
            label="Mask/Threshold",
            info_text="Masking methods either with a file input or a threshold",
            option_name = 'no_arg',
            list_components=[self.component_mask, self.component_threshold],
            cli=prepare_fieldmap_cli
        )

        path_output = os.path.join(CURR_DIR, "output_fieldmap")
        input_text_box_metadata_output = [
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "fieldmap.nii.gz"),
                "name": "output",
                "required": True
            }
        ]
        self.component_output = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_output,
            cli=prepare_fieldmap_cli
        )

        input_text_box_metadata_input2 = [
            {
                "button_label": "Input Magnitude",
                "button_function": "select_from_overlay",
                "name": "mag",
                "required": True
            }
        ]
        self.component_input2 = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_input2,
            cli=prepare_fieldmap_cli
        )

        self.run_component = RunComponent(
            panel=self,
            list_components=[self.component_input, self.component_input2, self.dropdown_mask_threshold,
                             self.dropdown_unwrapper, self.component_output],
            st_function="st_prepare_fieldmap"
        )

        return self.run_component.sizer


class MaskTab(Tab):
    def __init__(self, parent, title="Mask"):
        description = "Create a mask.\n\n" \
                      "Select a shape or an algorithm from the dropdown list."
        super().__init__(parent, title, description)

        self.sizer_run = self.create_sizer_run()
        self.positions = {}
        self.dropdown_metadata = [
            {
                "name": "Threshold",
                "sizer_function": self.create_sizer_threshold
            },
            {
                "name": "Rectangle",
                "sizer_function": self.create_sizer_rect
            },
            {
                "name": "Box",
                "sizer_function": self.create_sizer_box
            },
            {
                "name": "Sphere",
                "sizer_function": self.create_sizer_sphere
            }
        ]
        self.dropdown_choices = [item["name"] for item in self.dropdown_metadata]
        self.create_choice_box()

        self.create_dropdown_sizers()
        self.parent_sizer = self.create_sizer()
        self.SetSizer(self.parent_sizer)

        # Run on choice to select the default choice from the choice box widget
        self.on_choice(None)

    def create_dropdown_sizers(self):
        for dropdown_dict in self.dropdown_metadata:
            sizer = dropdown_dict["sizer_function"]()
            self.sizer_run.Add(sizer, 0, wx.EXPAND)
            self.positions[dropdown_dict["name"]] = self.sizer_run.GetItemCount() - 1

    def on_choice(self, event):
        # Get the selection from the choice box widget
        if self.choice_box.GetSelection() < 0:
            selection = self.choice_box.GetString(0)
            self.choice_box.SetSelection(0)
        else:
            selection = self.choice_box.GetString(self.choice_box.GetSelection())

        # Unshow everything then show the correct item according to the choice box
        self.unshow_choice_box_sizers()
        if selection in self.positions.keys():
            sizer_item = self.sizer_run.GetItem(self.positions[selection])
            sizer_item.Show(True)
        else:
            pass

        # Update the window
        self.SetVirtualSize(self.sizer_run.GetMinSize())
        self.Layout()

    def unshow_choice_box_sizers(self):
        """Set the Show variable to false for all sizers of the choice box widget"""
        for position in self.positions.values():
            sizer = self.sizer_run.GetItem(position)
            sizer.Show(False)

    def create_choice_box(self):
        self.choice_box = wx.Choice(self, choices=self.dropdown_choices)
        self.choice_box.Bind(wx.EVT_CHOICE, self.on_choice)
        self.sizer_run.Add(self.choice_box)
        self.sizer_run.AddSpacer(10)

    def create_sizer_threshold(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "output_mask_threshold")
        input_text_box_metadata = [
            {
                "button_label": "Input",
                "button_function": "select_from_overlay",
                "name": "input",
                "required": True
            },
            {
                "button_label": "Threshold",
                "default_text": "30",
                "name": "thr",
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
            }
        ]
        component = InputComponent(self, input_text_box_metadata, cli=threshold)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_mask threshold"
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_rect(self):
        path_output = os.path.join(CURR_DIR, "output_mask_rect")
        input_text_box_metadata = [
            {
                "button_label": "Input",
                "button_function": "select_from_overlay",
                "name": "input",
                "required": True
            },
            {
                "button_label": "Size",
                "name": "size",
                "n_text_boxes": 2,
                "required": True
            },
            {
                "button_label": "Center",
                "name": "center",
                "n_text_boxes": 2,
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
            }
        ]
        component = InputComponent(self, input_text_box_metadata, cli=rect)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_mask rect"
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_box(self):
        path_output = os.path.join(CURR_DIR, "output_mask_box")
        input_text_box_metadata = [
            {
                "button_label": "Input",
                "button_function": "select_from_overlay",
                "name": "input",
                "required": True
            },
            {
                "button_label": "Size",
                "name": "size",
                "n_text_boxes": 3,
                "required": True
            },
            {
                "button_label": "Center",
                "name": "center",
                "n_text_boxes": 3,
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
            }
        ]
        component = InputComponent(self, input_text_box_metadata, box)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_mask box"
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_sphere(self):
        path_output = os.path.join(CURR_DIR, "output_mask_sphere")
        input_text_box_metadata = [
            {
                "button_label": "Input",
                "button_function": "select_from_overlay",
                "name": "input",
                "required": True
            },
            {
                "button_label": "Radius",
                "name": "radius",
                "required": True
            },
            {
                "button_label": "Center",
                "name": "center",
                "n_text_boxes": 3,
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
            }
        ]
        component = InputComponent(self, input_text_box_metadata, sphere)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_mask sphere"
        )
        sizer = run_component.sizer
        return sizer


class DicomToNiftiTab(Tab):
    def __init__(self, parent, title="Dicom to Nifti"):
        description = "Convert DICOM files into NIfTI following the BIDS data structure"
        super().__init__(parent, title, description)

        self.sizer_run = self.create_sizer_run()
        sizer = self.create_dicom_to_nifti_sizer()
        self.sizer_run.Add(sizer, 0, wx.EXPAND)

        self.parent_sizer = self.create_sizer()
        self.SetSizer(self.parent_sizer)

    def create_dicom_to_nifti_sizer(self):
        path_output = os.path.join(CURR_DIR, "output_dicom_to_nifti")
        input_text_box_metadata = [
            {
                "button_label": "Input Folder",
                "button_function": "select_folder",
                "name": "input",
                "required": True
            },
            {
                "button_label": "Subject Name",
                "name": "subject",
                "required": True
            },
            {
                "button_label": "Config Path",
                "button_function": "select_file",
                "default_text": os.path.join(ST_DIR, "dcm2bids.json"),
                "name": "config",
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
            }
        ]
        component = InputComponent(self, input_text_box_metadata, cli=dicom_to_nifti_cli)
        run_component = RunComponent(panel=self, list_components=[component], st_function="st_dicom_to_nifti")
        return run_component.sizer


def read_image(filename, bitdepth=8):
    """Read image and convert it to desired bitdepth without truncation."""
    if 'tif' in str(filename):
        raw_img = imageio.imread(filename, format='tiff-pil')
        if len(raw_img.shape) > 2:
            raw_img = imageio.imread(filename, format='tiff-pil', as_gray=True)
    else:
        raw_img = imageio.imread(filename)
        if len(raw_img.shape) > 2:
            raw_img = imageio.imread(filename, as_gray=True)

    img = imageio.core.image_as_uint(raw_img, bitdepth=bitdepth)
    return img


def write_image(filename, img, format='png'):
    """Write image."""
    imageio.imwrite(filename, img, format=format)


def load_png_image_from_path(fsl_panel, image_path, is_mask=False, add_to_overlayList=True, colormap="greyscale"):
    """Convert a 2D image into a NIfTI image and load it as an overlay.

    The parameter ``add_to_overlayList`` enables displaying the overlay in FSLeyes.

    Args:
        image_path (str): The location of the image, including the name and the .extension
        is_mask (bool): (optional) Whether or not this is a segmentation mask. It will be
            treated as a normalads_utils
        add_to_overlayList (bool): (optional) Whether or not to add the image to the overlay
            list. If so, the image will be displayed in the application. This parameter is
            True by default.
        colormap (str): (optional) the colormap of image that will be displayed. This parameter
            is set to greyscale by default.

    Returns:
        overlay: the FSLeyes overlay corresponding to the loaded image.
    """

    # Open the 2D image
    img_png2d = read_image(image_path)

    if is_mask is True:
        img_png2d = img_png2d // np.iinfo(np.uint8).max  # Segmentation masks should be binary

    # Flip the image on the Y axis so that the morphometrics file shows the right coordinates
    img_png2d = np.flipud(img_png2d)

    # Convert image data into a NIfTI image
    # Note: PIL and NiBabel use different axis conventions, so some array manipulation has to be done.
    # TODO: save in the FOV of the current overlay
    nii_img = nib.Nifti1Image(
        np.rot90(img_png2d, k=1, axes=(1, 0)), np.eye(4)
    )

    # Save the NIfTI image in a temporary directory
    fname_out = image_path[:-3] + "nii.gz"
    nib.save(nii_img, fname_out)

    # Load the NIfTI image as an overlay
    img_overlay = loadoverlay.loadOverlays(paths=[fname_out], inmem=True, blocking=True)[0]

    # Display the overlay
    if add_to_overlayList is True:
        fsl_panel.overlayList.append(img_overlay)
        opts = fsl_panel.displayCtx.getOpts(img_overlay)
        opts.cmap = colormap

    return img_overlay
