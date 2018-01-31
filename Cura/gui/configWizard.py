#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import platform

import wx
import wx.wizard
import wx.lib.hyperlink as hl

from Cura.util import profile
from Cura.util import resources

class ConfigurationPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent):
		wx.wizard.WizardPageSimple.__init__(self, parent)
		contact_url = profile.getPreference('contact_url')

		sizer = wx.BoxSizer(wx.VERTICAL)

		title = wx.StaticText(self, -1, _("Configuration Cura by Dagoma"))
		title.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))

		sizer.Add(title, flag=wx.ALIGN_CENTRE)
		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Dagoma would like to thank you for your trust.")))
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Which printer do you use?")), flag=wx.BOTTOM, border=5)

		printers = resources.getPrinterOptions(profile.getPreference('internal_use'))
		printersImgs = []
		printersRadios = []
		firstLoad = True
		for printer in printers:
			img = wx.Image(resources.getPathForImage(printer.get('img')), wx.BITMAP_TYPE_ANY)
			bitmap = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img))
			printersImgs.append(bitmap)

			if firstLoad:
				radio = wx.RadioButton(self, -1, printer.get('desc'), style=wx.RB_GROUP)
				radio.SetValue(True)
				profile.putPreference('xml_file', printer.get('config'))
				firstLoad = False
			else:
				radio = wx.RadioButton(self, -1, printer.get('desc'))

			def OnPrinterSelect(e, config=printer.get('config')):
				profile.putPreference('xml_file', config)

			radio.Bind(wx.EVT_RADIOBUTTON, OnPrinterSelect)
			printersRadios.append(radio)

		printersSizer = wx.GridSizer(2, len(printers), 0)
		for bitmap in printersImgs:
			printersSizer.Add(bitmap, flag=wx.ALIGN_CENTER)

		for radio in printersRadios:
			printersSizer.Add(radio, flag=wx.ALIGN_CENTER)

		sizer.Add(printersSizer)

		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("The Cura by Dagoma software is now ready to use with your 3D printer.")))
		sizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Feel free to contact us!"), URL=contact_url))
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Enjoy!")))

		self.SetSizerAndFit(sizer)

	def AllowNext(self):
		return True

	def AllowBack(self):
		return False

class ConfigWizard(wx.wizard.Wizard):
	def __init__(self):
		super(ConfigWizard, self).__init__(None, -1, _("Configuration wizard"))

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.OnPageFinished)

		self.configurationPage = ConfigurationPage(self)

		self.FitToPage(self.configurationPage)
		self.GetPageAreaSizer().Add(self.configurationPage)
		self.RunWizard(self.configurationPage)
		if self:
			self.Destroy()

	def OnPageChanged(self, e):
		prev_btn = self.FindWindowById(wx.ID_BACKWARD)
		next_btn = self.FindWindowById(wx.ID_FORWARD)
		cancel_btn = self.FindWindowById(wx.ID_CANCEL)
		prev_btn.SetLabel(_('< Back'))
		cancel_btn.SetLabel(_('Cancel'))
		if self.HasNextPage(e.GetPage()):
			next_btn.SetLabel(_('Next >'))
		else:
			next_btn.SetLabel(_('Finish'))
			cancel_btn.Disable()
		if e.GetPage().AllowNext():
			next_btn.Enable()
		else:
			next_btn.Disable()
		if e.GetPage().AllowBack():
			prev_btn.Enable()
		else:
			prev_btn.Disable()

	def OnPageFinished(self, e):
		print "Configuration wizard finished..."
