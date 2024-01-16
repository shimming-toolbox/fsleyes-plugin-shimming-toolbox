import wx
from fsleyes_plugin_shimming_toolbox.components.component import Component
from fsleyes_plugin_shimming_toolbox.components.input_component import InputComponent
from fsleyes_plugin_shimming_toolbox.text_with_button import create_info_icon


class CheckboxComponent(Component):
    def __init__(self, panel, label, checkbox_metadata, option_name, components_dict={}, info_text=None):
        """
        Args:
            list_components (list): list of Components
            component_to_dropdown_choice (list): Tells which component associates with which dropdown selection.
                                                 If None, assumes 1:1.
        """
        self.sizer = self.create_sizer()

        self.checkbox_metadata = checkbox_metadata
        self.option_name = option_name

        self.panel = panel
        self.label = label
        self.info_text = info_text
        self.children = components_dict

        self.create_display()

    def create_display(self):
        # Button
        self.info_icon = create_info_icon(self.panel, self.info_text)
        self.button = wx.Button(self.panel, -1, label=self.label)

        # Checkboxes
        self.checkboxes = []
        for metadata in self.checkbox_metadata:
            self.checkboxes.append(wx.CheckBox(self.panel, label=metadata["label"]))

        # Add checkboxes to sizer
        self.checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.checkbox_sizer.Add(self.info_icon, 0, wx.ALIGN_LEFT | wx.RIGHT, 7)
        self.checkbox_sizer.Add(self.button, 0, wx.ALIGN_LEFT | wx.RIGHT, 10)
        for checkbox in self.checkboxes:
            # Bind
            checkbox.Bind(wx.EVT_CHECKBOX, self.show_children_sizers)
            self.checkbox_sizer.Add(checkbox, 0, wx.ALL, 5)        # Add to sizer + spacer below

        self.sizer.Add(self.checkbox_sizer)
        self.sizer.AddSpacer(10)

        # Add children
        self.add_children()

        wx.CallAfter(self.show_children_sizers, None)

    def add_children(self):
        for child in self.children:
            self.sizer.Add(child['object'].sizer, 0, wx.EXPAND)

    def show_children_sizers(self, event):
        childrens_to_show = self.get_children_to_show()
        for child in self.children:
            if child['object'] in childrens_to_show:
                child['object'].sizer.ShowItems(True)
            else:
                child['object'].sizer.ShowItems(False)
        self.panel.SetVirtualSize(self.panel.sizer_run.GetMinSize())
        self.panel.Layout()

    def get_children_to_show(self):
        """Get the children to show based on the checkbox selection"""
        checked_indices = {checkbox.GetLabel() for checkbox in self.checkboxes if checkbox.GetValue()}
        children_to_show = [child['object'] for child in self.children if set(child['checkbox']).intersection(checked_indices)]

        return children_to_show

    def create_sizer(self):
        """Create the centre sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        return sizer

    def get_command(self):
        command = []
        output = None
        overlay = []
        args = ""
        for checkbox in self.checkboxes:
            if checkbox.GetValue():
                label = checkbox.GetLabel()
                if label == 'f0':
                    args += '0,'
                else:
                    args += str(checkbox.GetLabel()) + ','

        if self.option_name == "arg":
            command.append(args[:-1])
        else:
            command.extend(['--' + self.option_name, args[:-1]])

        children_to_return = self.get_children_to_show()
        for child in children_to_return:
            if type(child) == InputComponent:
                cmd, output, overlay = child.get_command()
            else:
                cmd, _, _ = child.get_command()

            command.extend(cmd)

        return command, output, overlay
