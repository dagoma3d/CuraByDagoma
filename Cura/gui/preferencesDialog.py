__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.gui import configWizard
from Cura.gui import configBase
from Cura.util import machineCom
from Cura.util import profile
from Cura.util import pluginInfo
from Cura.util import resources

class preferencesDialog(wx.Frame):
	def __init__(self, parent):
		super(preferencesDialog, self).__init__(parent, title=_("Preferences"), style=wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		wx.EVT_CLOSE(self, self.OnClose)

		self.parent = parent

		self.panel = configBase.configPanelBase(self)

		left, right, main = self.panel.CreateConfigPanel(self)

		if len(resources.getLanguageOptions()) > 1:
			configBase.SettingRow(left, 'language', map(lambda n: n[1], resources.getLanguageOptions()))

		if len(resources.getPrinterOptions()) > 1:
			configBase.SettingRow(left, 'xml_file', map(lambda n: n[0], resources.getPrinterOptions()))

		self.okButton = wx.Button(right, -1, 'Ok')
		right.GetSizer().Add(self.okButton, (right.GetSizer().GetRows(), 0), flag=wx.ALIGN_BOTTOM|wx.BOTTOM|wx.RIGHT, border=5)
		self.okButton.Bind(wx.EVT_BUTTON, lambda e: self.Close())

		main.Fit()
		self.Fit()

	def OnClose(self, e):
		#self.parent.reloadSettingPanels()
		self.Destroy()
