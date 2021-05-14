import wx
import os
import logging

logger = logging.getLogger(__name__)

CURR_DIR = os.getcwd()

DIR = os.path.dirname(__file__)


class TextWithButton:
    """Creates a button with an input text box.

    wx.BoxSizer:

        InfoIcon(wx.StaticBitmap) - info icon
        wx.Button - clickable input button
        [wx.TextCtrl] - input text box(es)
        wx.StaticBitmap - asterisk icon

    Attributes:

        panel: TODO
        button_label (str): label to be put on the button.
        button_function: function which gets called when the button is clicked on.
        default_text (str): (optional) default text to be displayed in the input text box.
        textctrl_list (list wx.TextCtrl): list of input text boxes, can be more than one in a row.
        n_text_boxes (int): number of input text boxes to create.
        name (str): TODO
        info_text (str): text to be displayed when hovering over the info icon; should describe
            what the button/input is for.
        required (bool): if this input is required or not. If True, a red asterisk will be
            placed next to the input text box to indicate this.
    """
    def __init__(self, panel, button_label, button_function, name="default", default_text="",
                 n_text_boxes=1, info_text="", required=False):
        self.panel = panel
        self.button_label = button_label
        self.button_function = button_function
        self.default_text = default_text
        self.textctrl_list = []
        self.n_text_boxes = n_text_boxes
        self.name = name
        self.info_text = info_text
        self.required = required

    def create(self):
        text_with_button_box = wx.BoxSizer(wx.HORIZONTAL)
        button = wx.Button(self.panel, -1, label=self.button_label)
        text_with_button_box.Add(
            create_info_icon(self.panel, self.info_text), 0, wx.ALIGN_LEFT | wx.RIGHT, 7
        )
        for i_text_box in range(0, self.n_text_boxes):
            textctrl = wx.TextCtrl(parent=self.panel, value=self.default_text, name=self.name)
            self.textctrl_list.append(textctrl)
            if i_text_box == 0:
                if self.button_function == "select_folder":
                    self.button_function = lambda event, ctrl=textctrl: select_folder(event, ctrl)
                elif self.button_function == "select_file":
                    self.button_function = lambda event, ctrl=textctrl: select_file(event, ctrl)
                elif self.button_function == "select_from_overlay":
                    self.button_function = lambda event, panel=self.panel, ctrl=textctrl: \
                        select_from_overlay(event, panel, ctrl)
                elif self.button_function == "add_input_phase_boxes":
                    self.button_function = lambda event, panel=self.panel, ctrl=textctrl: \
                        add_input_phase_boxes(event, panel, ctrl)
                    textctrl.Bind(wx.EVT_TEXT, self.button_function)
                button.Bind(wx.EVT_BUTTON, self.button_function)
                text_with_button_box.Add(button, 0, wx.ALIGN_LEFT | wx.RIGHT, 10)

            text_with_button_box.Add(textctrl, 1, wx.ALIGN_LEFT | wx.LEFT, 10)
            if self.required:
                text_with_button_box.Add(
                    create_asterisk_icon(self.panel), 0, wx.ALIGN_RIGHT | wx.RIGHT, 7
                )

        return text_with_button_box


def create_asterisk_icon(panel):
    bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION)
    info_icon = os.path.join(DIR, 'img', 'asterisk.png')
    img = wx.Image(info_icon, wx.BITMAP_TYPE_ANY)
    bmp = img.ConvertToBitmap()
    image = wx.StaticBitmap(panel, bitmap=bmp)
    return image


def create_info_icon(panel, info_text=""):
    bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION)
    info_icon = os.path.join(DIR, 'img', 'info-icon.png')
    img = wx.Image(info_icon, wx.BITMAP_TYPE_ANY)
    bmp = img.ConvertToBitmap()
    image = InfoIcon(panel, bitmap=bmp, info_text=info_text)
    image.Bind(wx.EVT_MOTION, on_info_icon_mouse_over)
    return image


def on_info_icon_mouse_over(event):
    image = event.GetEventObject()
    tooltip = wx.ToolTip(image.info_text)
    tooltip.SetDelay(10)
    image.SetToolTip(tooltip)


class InfoIcon(wx.StaticBitmap):
    def __init__(self, panel, bitmap, info_text):
        self.info_text = info_text
        super(wx.StaticBitmap, self).__init__(panel, bitmap=bitmap)


def add_input_phase_boxes(event, tab, ctrl):
    """On click of ``Number of Echoes`` button, add ``n_echoes`` ``TextWithButton`` boxes.

    For this function, we are assuming the layout of the Component input is as follows:

        0 - Number of Echoes TextWithButton sizer
        1 - Spacer
        2 - next item, and so on

    First, we check and see how many phase boxes the tab currently has, and remove any where
    n current > n update.
    Next, we add n = n update - n current phase boxes to the tab.

    Args:
        event (wx.Event): when the ``Number of Echoes`` button is clicked.
        tab (FieldMapTab): tab class instance for ``Field Map``.
        ctrl (wx.TextCtrl): the text box containing the number of phase boxes to add. Must be an
            integer > 0.
    """
    option_name = "arg"
    try:
        n_echoes = int(ctrl.GetValue())
        if n_echoes < 1:
            raise Exception()
    except Exception:
        tab.terminal_component.log_to_terminal(
            "Number of Echoes must be an integer > 0",
            level="ERROR"
        )
        return

    insert_index = 2
    if n_echoes < tab.n_echoes:
        for index in range(tab.n_echoes, n_echoes, -1):
            tab.component_input.sizer.Hide(index + 1)
            tab.component_input.sizer.Remove(index + 1)
            tab.component_input.remove_last_input_text_box(option_name)

    for index in range(tab.n_echoes, n_echoes):
        text_with_button = TextWithButton(
            panel=tab,
            button_label=f"Input Phase {index + 1}",
            button_function="select_from_overlay",
            default_text="",
            n_text_boxes=1,
            name=f"input_phase_{index + 1}",
            info_text=f"Input path of phase nifti file {index + 1}",
            required=True
        )
        if index + 1 == n_echoes and tab.n_echoes == 0:
            tab.component_input.insert_input_text_box(
                text_with_button,
                option_name,
                index=insert_index + index,
                last=True)
        else:
            tab.component_input.insert_input_text_box(
                text_with_button,
                option_name,
                index=insert_index + index
            )

    tab.n_echoes = n_echoes
    tab.Layout()


def select_folder(event, ctrl):
    """Select a file folder from system path."""
    dlg = wx.DirDialog(None, "Choose Directory", CURR_DIR,
                       wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

    if dlg.ShowModal() == wx.ID_OK:
        folder = dlg.GetPath()
        ctrl.SetValue(folder)
        logger.info(f"Folder set to: {folder}")


def select_file(event, ctrl):
    """Select a file from system path."""
    dlg = wx.FileDialog(parent=None,
                        message="Select File",
                        defaultDir=CURR_DIR,
                        style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        ctrl.SetValue(path)
        logger.info(f"File set to: {path}")


def select_from_overlay(event, tab, ctrl):
    """Fetch path to file highlighted in the Overlay list.

    Args:
        event (wx.Event): event passed to a callback or member function.
        tab (Tab): Must be a subclass of the Tab class
        ctrl (wx.TextCtrl): the text item.
    """

    # This is messy and wont work if we change any class hierarchy.. using GetTopLevelParent() only
    # works if the pane is not floating
    # Get the displayCtx class initialized in STControlPanel
    window = tab.GetGrandParent().GetParent()
    selected_overlay = window.displayCtx.getSelectedOverlay()
    if selected_overlay is not None:
        filename_path = selected_overlay.dataSource
        ctrl.SetValue(filename_path)
    else:
        tab.terminal_component.log_to_terminal(
            "Import and select an image from the Overlay list",
            level="INFO"
        )
