import wx
import os
from fsleyes_plugin_shimming_toolbox.components import InfoComponent, TerminalComponent, \
    DropdownComponent, RunComponent, InputComponent

CURR_DIR = os.getcwd()


class Tab(wx.Panel):
    def __init__(self, parent, title, description):
        wx.Panel.__init__(self, parent)
        self.title = title
        self.sizer_info = InfoComponent(self, description).sizer

    def create_sizer(self):
        """Create the parent sizer for the tab.

        Tab is divided into 3 main sizers:
            sizer_info | sizer_run | sizer_terminal
        """
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_info)
        sizer.AddSpacer(30)
        sizer.Add(self.sizer_run, wx.EXPAND)
        sizer.AddSpacer(30)
        sizer.Add(self.sizer_terminal, wx.EXPAND)
        return sizer


class ShimTab(Tab):
    def __init__(self, parent, title="Shim"):

        description = "Perform B0 shimming.\n\n" \
                      "Select the shimming algorithm from the dropdown list."
        super().__init__(parent, title, description)

        self.sizer_run = self.create_sizer_run()
        self.positions = {}
        self.dropdown_metadata = [
            {
                "name": "RT_ZShim",
                "sizer_function": self.create_sizer_zshim
            },
            {
                "name": "Nothing",
                "sizer_function": self.create_sizer_other_algo
            }
        ]
        self.dropdown_choices = [item["name"] for item in self.dropdown_metadata]

        self.create_choice_box()

        self.terminal_component = TerminalComponent(self)
        self.sizer_terminal = self.terminal_component.sizer

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
        selection = self.choice_box.GetString(self.choice_box.GetSelection())

        # Unshow everything then show the correct item according to the choice box
        self.unshow_choice_box_sizers()
        if selection in self.positions.keys():
            sizer_item = self.sizer_run.GetItem(self.positions[selection])
            sizer_item.Show(True)
        else:
            pass

        # Update the window
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

    def create_sizer_zshim(self, metadata=None):
        path_output = os.path.join(CURR_DIR, "output_rt_zshim")
        input_text_box_metadata = [
            {
                "button_label": "Input Fieldmap",
                "name": "fmap",
                "button_function": "select_from_overlay",
                "info_text": "B0 fieldmap. This should be a 4D file (4th dimension being time).",
                "required": True
            },
            {
                "button_label": "Input Anat",
                "name": "anat",
                "button_function": "select_from_overlay",
                "info_text": "Filename of the anatomical image to apply the correction.",
                "required": True
            },
            {
                "button_label": "Input Static Mask",
                "name": "mask-static",
                "button_function": "select_from_overlay",
                "info_text": """3D NIfTI file used to define the static spatial region to shim.
                    The coordinate system should be the same as anat's coordinate system."""
            },
            {
                "button_label": "Input RIRO Mask",
                "name": "mask-riro",
                "button_function": "select_from_overlay",
                "info_text": """3D NIfTI file used to define the time varying (i.e. RIRO,
                    Respiration-Induced Resonance Offset) spatial region to shim.
                    The coordinate system should be the same as anat's coordinate system."""
            },
            {
                "button_label": "Input Respiratory Trace",
                "button_function": "select_file",
                "name": "resp",
                "info_text": "Siemens respiratory file containing pressure data.",
                "required": True
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
                "info_text": "Directory to output gradient text file and figures."
            }
        ]

        component = InputComponent(self, input_text_box_metadata)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_realtime_zshim",
            output_paths=[
                os.path.join(path_output, "fig_resampled_riro.nii.gz"),
                os.path.join(path_output, "fig_resampled_static.nii.gz")
            ]
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_other_algo(self):
        sizer_shim_default = wx.BoxSizer(wx.VERTICAL)
        description_text = wx.StaticText(self, id=-1, label="Not implemented")
        sizer_shim_default.Add(description_text)
        return sizer_shim_default

    def create_sizer_run(self):
        """Create the centre sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(400, 300)
        sizer.AddSpacer(10)
        return sizer


class FieldMapTab(Tab):
    def __init__(self, parent, title="Field Map"):
        description = "Create a B0 fieldmap.\n\n" \
                      "Enter the Number of Echoes then press the `Number of Echoes` button.\n\n" \
                      "Select the unwrapper from the dropdown list."
        super().__init__(parent, title, description)
        self.n_echoes = 0
        input_text_box_metadata_input = [
            {
                "button_label": "Number of Echoes",
                "button_function": "add_input_phase_boxes",
                "name": "no_arg",
                "info_text": "Number of phase NIfTI files to be used. Must be an integer > 0.",
                "required": True
            }
        ]
        dropdown_metadata = [
            {
                "label": "prelude",
                "option_name": "unwrapper",
                "option_value": "prelude"
            },
            {
                "label": "Nothing",
                "option_name": "unwrapper",
                "option_value": "QGU"
            }
        ]
        path_output = os.path.join(CURR_DIR, "output_fieldmap")

        input_text_box_metadata_prelude = [
            {
                "button_label": "Input Magnitude",
                "button_function": "select_from_overlay",
                "name": "mag",
                "info_text": "Input path of mag NIfTI file.",
                "required": True
            },
            {
                "button_label": "Threshold",
                "name": "threshold",
                "info_text": "Float threshold for masking. Used for: PRELUDE."
            },
            {
                "button_label": "Input Mask",
                "button_function": "select_from_overlay",
                "name": "mask",
                "info_text": "Input path for a mask. Used for PRELUDE"
            }
        ]
        input_text_box_metadata_other = [
            {
                "button_label": "Other",
                "name": "other",
                "info_text": "TODO"
            }
        ]
        input_text_box_metadata_output = [
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "fieldmap.nii.gz"),
                "name": "output",
                "info_text": "Output filename for the fieldmap, supported types : '.nii', '.nii.gz'",
                "required": True
            }
        ]

        self.terminal_component = TerminalComponent(panel=self)
        self.component_input = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_input
        )
        self.component_prelude = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_prelude
        )
        self.component_other = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_other
        )
        self.dropdown = DropdownComponent(
            panel=self,
            dropdown_metadata=dropdown_metadata,
            list_components=[self.component_prelude, self.component_other],
            name="Unwrapper",
            info_text="Algorithm for unwrapping"
        )
        self.component_output = InputComponent(
            panel=self,
            input_text_box_metadata=input_text_box_metadata_output
        )
        self.run_component = RunComponent(
            panel=self,
            list_components=[self.component_input, self.dropdown, self.component_output],
            st_function="st_prepare_fieldmap"
        )
        self.sizer_run = self.run_component.sizer
        self.sizer_terminal = self.terminal_component.sizer
        sizer = self.create_sizer()
        self.SetSizer(sizer)


class MaskTab(Tab):
    def __init__(self, parent, title="Mask"):
        description = "Create a mask based.\n\n" \
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
            }
        ]
        self.dropdown_choices = [item["name"] for item in self.dropdown_metadata]
        self.create_choice_box()

        self.terminal_component = TerminalComponent(self)
        self.sizer_terminal = self.terminal_component.sizer

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
        selection = self.choice_box.GetString(self.choice_box.GetSelection())

        # Unshow everything then show the correct item according to the choice box
        self.unshow_choice_box_sizers()
        if selection in self.positions.keys():
            sizer_item = self.sizer_run.GetItem(self.positions[selection])
            sizer_item.Show(True)
        else:
            pass

        # Update the window
        self.Layout()
        self.GetParent().Layout()

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
                "info_text": """Input path of the nifti file to mask. Supported extensions are
                    .nii or .nii.gz.""",
                "required": True
            },
            {
                "button_label": "Threshold",
                "default_text": "30",
                "name": "thr",
                "info_text": """Integer value to threshold the data: voxels will be set to zero if
                    their value <= this threshold. Default = 30."""
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
                "info_text": """Name of output mask. Supported extensions are .nii or .nii.gz."""
            }
        ]
        component = InputComponent(self, input_text_box_metadata)
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
                "info_text": """Input path of the NIfTI file to mask. The NIfTI file must be 2D or
                    3D. Supported extensions are .nii or .nii.gz.""",
                "required": True
            },
            {
                "button_label": "Size",
                "name": "size",
                "n_text_boxes": 2,
                "info_text": "Length of the side of the box along 1st & 2nd dimension (in pixels).",
                "required": True
            },
            {
                "button_label": "Center",
                "name": "center",
                "n_text_boxes": 2,
                "info_text": """Center of the box along first and second dimension (in pixels).
                    If no center is provided (None), the middle is used."""
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
                "info_text": """Name of output mask. Supported extensions are .nii or .nii.gz."""
            }
        ]
        component = InputComponent(self, input_text_box_metadata)
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
                "info_text": """Input path of the NIfTI file to mask. The NIfTI file must be 3D.
                    Supported extensions are .nii or .nii.gz.""",
                "required": True
            },
            {
                "button_label": "Size",
                "name": "size",
                "n_text_boxes": 3,
                "info_text": "Length of side of box along 1st, 2nd, & 3rd dimension (in pixels).",
                "required": True
            },
            {
                "button_label": "Center",
                "name": "center",
                "n_text_boxes": 3,
                "info_text": """Center of the box along 1st, 2nd, & 3rd dimension (in pixels).
                    If no center is provided (None), the middle is used."""
            },
            {
                "button_label": "Output File",
                "button_function": "select_folder",
                "default_text": os.path.join(path_output, "mask.nii.gz"),
                "name": "output",
                "info_text": """Name of output mask. Supported extensions are .nii or .nii.gz."""
            }
        ]
        component = InputComponent(self, input_text_box_metadata)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_mask box"
        )
        sizer = run_component.sizer
        return sizer

    def create_sizer_run(self):
        """Create the centre sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(400, 300)
        sizer.AddSpacer(10)
        return sizer


class DicomToNiftiTab(Tab):
    def __init__(self, parent, title="Dicom to Nifti"):
        description = "Process dicoms into NIfTI following the BIDS data structure"
        super().__init__(parent, title, description)
        path_output = os.path.join(CURR_DIR, "output_dicom_to_nifti")
        input_text_box_metadata = [
            {
                "button_label": "Input Folder",
                "button_function": "select_folder",
                "name": "input",
                "info_text": "Input path of dicom folder",
                "required": True
            },
            {
                "button_label": "Subject Name",
                "name": "subject",
                "info_text": "Name of the patient",
                "required": True
            },
            {
                "button_label": "Config Path",
                "button_function": "select_file",
                "default_text": os.path.join(CURR_DIR,
                                             "dcm2bids.json"),
                "name": "config",
                "info_text": "Full file path and name of the BIDS config file"
            },
            {
                "button_label": "Output Folder",
                "button_function": "select_folder",
                "default_text": path_output,
                "name": "output",
                "info_text": "Output path for NIfTI files."
            }
        ]
        self.terminal_component = TerminalComponent(self)
        component = InputComponent(self, input_text_box_metadata)
        run_component = RunComponent(
            panel=self,
            list_components=[component],
            st_function="st_dicom_to_nifti"
        )
        self.sizer_run = run_component.sizer
        self.sizer_terminal = self.terminal_component.sizer
        sizer = self.create_sizer()
        self.SetSizer(sizer)
