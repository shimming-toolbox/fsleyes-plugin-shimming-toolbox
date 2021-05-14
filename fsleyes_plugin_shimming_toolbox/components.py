import wx
import abc
import webbrowser
import os

import fsleyes.actions.loadoverlay as loadoverlay
from fsleyes_plugin_shimming_toolbox.utils import run_subprocess, get_folder, \
    load_png_image_from_path
from fsleyes_plugin_shimming_toolbox.text_with_button import TextWithButton, create_info_icon

DIR = os.path.dirname(__file__)


class Component:
    def __init__(self, panel, list_components=[]):
        self.panel = panel
        self.list_components = list_components

    @abc.abstractmethod
    def create_sizer(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'create_sizer') and
                callable(subclass.create_sizer) or
                NotImplemented)


class InfoComponent(Component):
    def __init__(self, panel, description):
        super().__init__(panel)
        self.description = description
        self.sizer = self.create_sizer()

    def create_sizer(self):
        """Create the left sizer containing generic Shimming Toolbox information."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        st_logo = self.get_logo()
        sizer.Add(st_logo, flag=wx.SHAPED, proportion=1)

        button_documentation = wx.Button(self.panel, label="Documentation",
                                         size=wx.Size(100, 20))
        button_documentation.Bind(wx.EVT_BUTTON, self.documentation_url)
        sizer.Add(button_documentation, flag=wx.SHAPED, proportion=1)

        description_text = wx.StaticText(self.panel, id=-1, label=self.description)
        width = st_logo.Size[0]
        description_text.Wrap(width)
        sizer.Add(description_text)
        return sizer

    def get_logo(self, scale=0.2):
        """Loads ShimmingToolbox logo saved as a png image and returns it as a wx.Bitmap image.

        Retunrs:
            wx.StaticBitmap: The ``ShimmingToolbox`` logo
        """
        fname_st_logo = os.path.join(DIR, 'img', 'shimming_toolbox_logo.png')

        png = wx.Image(fname_st_logo, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        png.SetSize((png.GetWidth()*scale, png.GetHeight()*scale))
        logo_image = wx.StaticBitmap(
            parent=self.panel,
            id=-1,
            bitmap=png,
            pos=wx.DefaultPosition
        )
        return logo_image

    def documentation_url(self, event):
        """Redirect ``documentation_button`` to the ``shimming-toolbox`` page."""
        url = "https://shimming-toolbox.org/en/latest/"
        webbrowser.open(url)


class InputComponent(Component):
    def __init__(self, panel, input_text_box_metadata):
        super().__init__(panel)
        self.sizer = self.create_sizer()
        self.input_text_boxes = {}
        self.input_text_box_metadata = input_text_box_metadata
        self.add_input_text_boxes()

    def create_sizer(self):
        """Create the centre sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        return sizer

    def add_input_text_boxes(self, spacer_size=10):
        """Add a list of input text boxes (TextWithButton) to the sizer_input.

        Args:
            self.input_text_box_metadata (list)(dict): A list of dictionaries, where the dictionaries have two keys:
                ``button_label`` and ``button_function``.
                .. code::

                    {
                        "button_label": The label to go on the button.
                        "button_function": the class function (self.myfunc) which will get
                            called when the button is pressed. If no action is desired, create
                            a function that is just ``pass``.
                        "default_text": (optional) The default text to be displayed.
                        "name" : Option name in the CLI, use "arg" as the name for an argument.
                    }

            spacer_size (int): The size of the space to be placed between each input text box.

        """
        for twb_dict in self.input_text_box_metadata:
            text_with_button = TextWithButton(
                panel=self.panel,
                button_label=twb_dict["button_label"],
                button_function=twb_dict.get("button_function", self.button_do_something),
                default_text=twb_dict.get("default_text", ""),
                n_text_boxes=twb_dict.get("n_text_boxes", 1),
                name=twb_dict.get("name", "default"),
                info_text=twb_dict.get("info_text", ""),
                required=twb_dict.get("required", False)
            )
            self.add_input_text_box(text_with_button, twb_dict.get("name", "default"))

    def add_input_text_box(self, text_with_button, name, spacer_size=10):
        box = text_with_button.create()
        self.sizer.Add(box, 0, wx.EXPAND)
        self.sizer.AddSpacer(spacer_size)
        if name in self.input_text_boxes.keys():
            self.input_text_boxes[name].append(text_with_button)
        else:
            self.input_text_boxes[name] = [text_with_button]

    def insert_input_text_box(self, text_with_button, name, index, last=False, spacer_size=10):
        box = text_with_button.create()
        self.sizer.Insert(index=index, sizer=box, flag=wx.EXPAND)
        if last:
            self.sizer.InsertSpacer(index=index + 1, size=spacer_size)
        if name in self.input_text_boxes.keys():
            self.input_text_boxes[name].append(text_with_button)
        else:
            self.input_text_boxes[name] = [text_with_button]

    def remove_last_input_text_box(self, name):
        self.input_text_boxes[name].pop(-1)

    def button_do_something(self, event):
        """TODO"""
        pass


class DropdownComponent(Component):
    def __init__(self, panel, dropdown_metadata, name, list_components=[], info_text=""):
        """ Create a dropdown list

        Args:
            panel (wx.Panel): A panel is a window on which controls are placed.
            dropdown_metadata (list)(dict): A list of dictionaries where the dictionaries have the
                required keys: ``label``, ``option_name``, ``option_value``.
                .. code::

                    {
                        "label": The label for the dropdown box
                        "option_name": The name of the option in the CLI
                        "option_value": The value linked to the option in the CLI
                    }

            name (str): Label of the button describing the dropdown
            list_components (list): list of InputComponents
            info_text (str): Info message displayed when hovering over the "i" icon.
        """
        super().__init__(panel, list_components)
        self.dropdown_metadata = dropdown_metadata
        self.name = name
        self.info_text = info_text
        self.positions = {}
        self.input_text_boxes = {}
        self.sizer = self.create_sizer()
        self.dropdown_choices = [item["label"] for item in self.dropdown_metadata]
        self.create_choice_box()
        self.create_dropdown_sizers()
        self.on_choice(None)

    def create_dropdown_sizers(self):
        for index in range(len(self.dropdown_choices)):
            sizer = self.list_components[index].sizer
            self.sizer.Add(sizer, 0, wx.EXPAND)
            self.positions[self.dropdown_choices[index]] = self.sizer.GetItemCount() - 1

    def unshow_choice_box_sizers(self):
        """Set the Show variable to false for all sizers of the choice box widget"""
        for position in self.positions.values():
            sizer = self.sizer.GetItem(position)
            sizer.Show(False)

    def create_choice_box(self):
        self.choice_box = wx.Choice(self.panel, choices=self.dropdown_choices)
        self.choice_box.Bind(wx.EVT_CHOICE, self.on_choice)
        button = wx.Button(self.panel, -1, label=self.name)
        self.choice_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice_box_sizer.Add(create_info_icon(self.panel, self.info_text), 0, wx.ALIGN_LEFT | wx.RIGHT, 7)
        self.choice_box_sizer.Add(button, 0, wx.ALIGN_LEFT | wx.RIGHT, 10)
        self.choice_box_sizer.Add(self.choice_box)
        self.sizer.Add(self.choice_box_sizer)
        self.sizer.AddSpacer(10)

    def on_choice(self, event):
        # Get the selection from the choice box widget
        selection = self.choice_box.GetString(self.choice_box.GetSelection())

        # Unshow everything then show the correct item according to the choice box
        self.unshow_choice_box_sizers()
        if selection in self.positions.keys():
            sizer_item_threshold = self.sizer.GetItem(self.positions[selection])
            sizer_item_threshold.Show(True)
        else:
            pass

        index = self.find_index(selection)
        self.input_text_boxes = self.list_components[index].input_text_boxes
        self.input_text_boxes[self.dropdown_metadata[index]["option_name"]] = \
            [self.dropdown_metadata[index]["option_value"]]

        # Update the window
        self.panel.Layout()

    def find_index(self, label):
        for index in range(len(self.dropdown_metadata)):
            if self.dropdown_metadata[index]["label"] == label:
                return index

    def create_sizer(self):
        """Create the a sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        return sizer


class RunComponent(Component):
    """Component which contains input and run button.

    Attributes:
        panel (wx.Panel): TODO.
        st_function (str): Name of the ``Shimming Toolbox`` CLI function to be called.
        list_components (list of Component): list of subcomponents to be added.
        output_paths (list of str): file or folder paths containing output from ``st_function``.

    """
    def __init__(self, panel, st_function, list_components=[], output_paths=[]):
        super().__init__(panel, list_components)
        self.st_function = st_function
        self.sizer = self.create_sizer()
        self.add_button_run()
        self.output_paths_original = output_paths
        self.output_paths = output_paths.copy()

    def create_sizer(self):
        """Create the centre sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(400, 300)
        sizer.AddSpacer(10)
        for component in self.list_components:
            sizer.Add(component.sizer, 0, wx.EXPAND)
        return sizer

    def add_button_run(self):
        """Add the run button which will call the ``Shimming Toolbox`` CLI."""
        button_run = wx.Button(self.panel, -1, label="Run")
        button_run.Bind(wx.EVT_BUTTON, self.button_run_on_click)
        self.sizer.Add(button_run, 0, wx.CENTRE)
        self.sizer.AddSpacer(10)

    def button_run_on_click(self, event):
        """Function called when the ``Run`` button is clicked.

        1. Calls the relevant ``Shimming Toolbox`` CLI command (``st_function``)
        2. Logs the output to the terminal in the GUI.
        3. Sends the output files to the overlay list if applicable.

        """
        try:
            command, msg = self.get_run_args(self.st_function)
            self.panel.terminal_component.log_to_terminal(msg, level="INFO")
            self.create_output_folder()
            run_subprocess(command)
            msg = f"Run {self.st_function} completed successfully"
            self.panel.terminal_component.log_to_terminal(msg, level="INFO")
            self.send_output_to_overlay()
        except Exception as err:
            self.panel.terminal_component.log_to_terminal(str(err), level="ERROR")

        self.output_paths.clear()
        self.output_paths = self.output_paths_original.copy()

    def send_output_to_overlay(self):
        for output_path in self.output_paths:
            if os.path.isfile(output_path):
                try:
                    # Display the overlay
                    window = self.panel.GetGrandParent().GetParent()
                    if output_path[-4:] == ".png":
                        load_png_image_from_path(window, output_path, colormap="greyscale")
                    elif output_path[-7:] == ".nii.gz" or output_path[-4:] == ".nii":
                        # Load the NIfTI image as an overlay
                        img_overlay = loadoverlay.loadOverlays(
                            paths=[output_path],
                            inmem=True,
                            blocking=True)[0]
                        window.overlayList.append(img_overlay)
                except Exception as err:
                    self.panel.terminal_component.log_to_terminal(str(err), level="ERROR")

    def create_output_folder(self):
        """Recursively create output folder if it does not exist."""
        for output_path in self.output_paths:
            output_folder = get_folder(output_path)
            if not os.path.exists(output_folder):
                self.panel.terminal_component.log_to_terminal(
                    f"Creating folder {output_folder}",
                    level="INFO"
                )
                os.makedirs(output_folder)

    def get_run_args(self, st_function):
        msg = "Running "
        command = st_function

        command_list_arguments = []
        command_dict_options = {}
        for component in self.list_components:
            for name, input_text_box_list in component.input_text_boxes.items():
                if name == "no_arg":
                    continue
                for input_text_box in input_text_box_list:
                    # Allows to chose from a dropdown
                    if type(input_text_box) == str:
                        if name in command_dict_options.keys():
                            command_dict_options[name].append(input_text_box)
                        else:
                            command_dict_options[name] = [input_text_box]
                    # Normal case where input_text_box is a TextwithButton
                    else:
                        for textctrl in input_text_box.textctrl_list:
                            arg = textctrl.GetValue()
                            if arg == "" or arg is None:
                                if input_text_box.required is True:
                                    raise RunArgumentErrorST(
                                        f"""Argument {name} is missing a value, please enter a
                                            valid input"""
                                    )
                            else:
                                # Case where the option name is set to arg, this handles it as if it were an argument
                                if name == "arg":
                                    command_list_arguments.append(arg)
                                # Normal options
                                else:
                                    if name == "output":
                                        self.output_paths.append(arg)
                                    if name in command_dict_options.keys():
                                        command_dict_options[name].append(arg)
                                    else:
                                        command_dict_options[name] = [arg]

        # Arguments don't need "-"
        for arg in command_list_arguments:
            command += f" {arg}"

        # Handles options
        for name, args in command_dict_options.items():
            command += f" -{name}"
            for arg in args:
                command += f" {arg}"
        msg += command
        return command, msg


class TerminalComponent(Component):
    def __init__(self, panel, list_components=[]):
        super().__init__(panel, list_components)
        self.terminal = None
        self.sizer = self.create_sizer()

    @property
    def terminal(self):
        return self._terminal

    @terminal.setter
    def terminal(self, terminal):
        if terminal is None:
            terminal = wx.TextCtrl(self.panel, wx.ID_ANY, size=(500, 300),
                                   style=wx.TE_MULTILINE | wx.TE_READONLY)
            terminal.SetDefaultStyle(wx.TextAttr(wx.WHITE, wx.BLACK))
            terminal.SetBackgroundColour(wx.BLACK)

        self._terminal = terminal

    def create_sizer(self):
        """Create the right sizer containing the terminal interface."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        sizer.Add(self.terminal)
        return sizer

    def log_to_terminal(self, msg, level=None):
        if level is None:
            self.terminal.AppendText(f"{msg}\n")
        else:
            self.terminal.AppendText(f"{level}: {msg}\n")


class RunArgumentErrorST(Exception):
    """Exception for missing input arguments for CLI call."""
    pass
