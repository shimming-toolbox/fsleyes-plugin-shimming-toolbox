import wx
from fsleyes_plugin_shimming_toolbox.components.component import Component
from fsleyes_plugin_shimming_toolbox.text_with_button import create_info_icon

class CheckboxComponent():
    def __init__(self, panel, label, info_text=None):
        # super().__init__(panel, label=label)
        self.sizer = self.create_sizer()
        self.panel = panel
        self.label = label
        self.info_text = info_text
        # Button
        self.info_icon = create_info_icon(self.panel, self.info_text)
        self.button = wx.Button(self.panel, -1, label=self.label)
        
        # Checkboxes
        self.checkbox_f0 = wx.CheckBox(self.panel, label="f0")
        self.checkbox_1 = wx.CheckBox(self.panel, label="1")
        self.checkbox_2 = wx.CheckBox(self.panel, label="2")
        
        # Add checkboxes to sizer
        self.checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.checkbox_sizer.Add(self.info_icon, 0, wx.ALIGN_LEFT | wx.RIGHT, 7)
        self.checkbox_sizer.Add(self.button, 0, wx.ALIGN_LEFT | wx.RIGHT, 10)
        self.checkbox_sizer.Add(self.checkbox_f0, 0, wx.ALL, 5)
        self.checkbox_sizer.Add(self.checkbox_1, 0, wx.ALL, 5)
        self.checkbox_sizer.Add(self.checkbox_2, 0, wx.ALL, 5)
        
        # Add to sizer + spacer below
        self.sizer.Add(self.checkbox_sizer)
        self.sizer.AddSpacer(10)
        
    def create_sizer(self):
        """Create the centre sizer containing tab-specific functionality."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        return sizer
    
