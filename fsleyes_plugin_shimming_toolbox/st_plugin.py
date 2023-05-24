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
import fsleyes.views.canvaspanel as canvaspanel
import logging
import os
import wx

from fsleyes_plugin_shimming_toolbox import __ST_DIR__, __CURR_DIR__
from fsleyes_plugin_shimming_toolbox.tabs.tab import Tab
from fsleyes_plugin_shimming_toolbox.tabs.b0shim_tab import B0ShimTab
from fsleyes_plugin_shimming_toolbox.components.dropdown_component import DropdownComponent
from fsleyes_plugin_shimming_toolbox.components.run_component import RunComponent
from fsleyes_plugin_shimming_toolbox.components.input_component import InputComponent

from shimmingtoolbox.cli.b1shim import b1shim_cli
from shimmingtoolbox.cli.dicom_to_nifti import dicom_to_nifti_cli
from shimmingtoolbox.cli.mask import box, rect, threshold, sphere
from shimmingtoolbox.cli.prepare_fieldmap import prepare_fieldmap_cli

logger = logging.getLogger(__name__)

VERSION = "0.1.1"


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
        path_output = os.path.join(__CURR_DIR__, "b1_shim_output")
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
        path_output = os.path.join(__CURR_DIR__, "b1_shim_output")
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
        path_output = os.path.join(__CURR_DIR__, "b1_shim_output")
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
        path_output = os.path.join(__CURR_DIR__, "b1_shim_output")
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

        path_output = os.path.join(__CURR_DIR__, "output_fieldmap")
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
        path_output = os.path.join(__CURR_DIR__, "output_mask_threshold")
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
        path_output = os.path.join(__CURR_DIR__, "output_mask_rect")
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
        path_output = os.path.join(__CURR_DIR__, "output_mask_box")
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
        path_output = os.path.join(__CURR_DIR__, "output_mask_sphere")
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
        path_output = os.path.join(__CURR_DIR__, "output_dicom_to_nifti")
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
                "default_text": os.path.join(__ST_DIR__, "dcm2bids.json"),
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
