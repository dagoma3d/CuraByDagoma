__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.util import resources
from Cura.util import profile

class printerWindow(wx.Frame):
	def __init__(self, parent):
		super(printerWindow, self).__init__(parent, title=_("Printer choice"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)
		self.parent = parent

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		wx.EVT_CLOSE(self, self.OnClose)

		p = wx.Panel(self)
		self.panel = p
		sizer = wx.BoxSizer()
		self.SetSizer(sizer)
		sizer.Add(p)
		sizer = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(sizer)

		title = wx.StaticText(p, -1, _("Configuration Cura by Dagoma"))
		title.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))

		sizer.Add(title, flag=wx.ALIGN_CENTRE)
		sizer.Add(wx.StaticLine(p, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(p, wx.ID_ANY, _("Which printer do you use?")), flag=wx.BOTTOM, border=5)

		printers = resources.getPrinterOptions(profile.getPreference('internal_use'))
		printersImgs = []
		printersRadios = []
		printersDescs = []
		firstItem = True
		for printer in printers:
			img = wx.Image(resources.getPathForImage(printer.get('img')), wx.BITMAP_TYPE_ANY)
			bitmap = wx.StaticBitmap(p, -1, wx.BitmapFromImage(img))
			printersImgs.append(bitmap)

			if firstItem:
				radio = wx.RadioButton(p, -1, printer.get('name'), style=wx.RB_GROUP)
			else:
				radio = wx.RadioButton(p, -1, printer.get('name'))

			if printer.get('config') == profile.getPreference('xml_file'):
				radio.SetValue(True)
			else:
				radio.SetValue(False)

			def OnPrinterSelect(e, config=printer.get('config')):
				profile.putPreference('xml_file', config)

			radio.Bind(wx.EVT_RADIOBUTTON, OnPrinterSelect)
			printersRadios.append(radio)

			desc_text = printer.get('desc')
			if desc_text != '':
				desc_text = _(desc_text)
			desc = wx.StaticText(p, -1, desc_text)
			printersDescs.append(desc)

			firstItem = False

		printersSizer = wx.FlexGridSizer(3, len(printers), 0, 0)
		printersSizer.SetFlexibleDirection(wx.VERTICAL)
		for bitmap in printersImgs:
			printersSizer.Add(bitmap, flag=wx.ALIGN_CENTER)

		for radio in printersRadios:
			printersSizer.Add(radio, flag=wx.ALIGN_CENTER)

		for desc in printersDescs:
			printersSizer.Add(desc, flag=wx.ALIGN_CENTER)

		sizer.Add(printersSizer)

		sizer.Add(wx.StaticLine(p, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		okButton = wx.Button(p, -1, 'Ok')
		okButton.Bind(wx.EVT_BUTTON, self.OnClose)
		sizer.Add(okButton, flag=wx.ALIGN_RIGHT)

		self.Fit()

	def OnClose(self, e):
		self.parent.ReloadSettingPanels()
		self.Destroy()
