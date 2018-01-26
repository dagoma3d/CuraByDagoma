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
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Which printer do you use?")))

		discoimg = wx.Image(resources.getPathForImage('discoeasy200.png'), wx.BITMAP_TYPE_ANY)
		easy200Radio = wx.RadioButton(self, -1, "DiscoEasy200", style=wx.RB_GROUP)
		easy200Radio.SetValue(True)
		profile.putPreference('xml_file', "discoeasy200.xml")
		easy200Radio.Bind(wx.EVT_RADIOBUTTON, self.OnDiscoEasy200Select)
		discosizer = wx.BoxSizer(wx.HORIZONTAL)


		nevaimg = wx.Image(resources.getPathForImage('neva.png'), wx.BITMAP_TYPE_ANY)
		nevaRadio = wx.RadioButton(self, -1, "Neva")
		nevaRadio.Bind(wx.EVT_RADIOBUTTON, self.OnNevaSelect)
		nevasizer = wx.BoxSizer(wx.HORIZONTAL)


		printersSizer = wx.GridSizer(2, 2, 2)
		printersSizer.Add(wx.StaticBitmap(self, -1, wx.BitmapFromImage(discoimg)), flag=wx.ALIGN_RIGHT)
		printersSizer.Add(easy200Radio, flag=wx.ALIGN_CENTER_VERTICAL)
		printersSizer.Add(wx.StaticBitmap(self, -1, wx.BitmapFromImage(nevaimg)), flag=wx.ALIGN_RIGHT)
		printersSizer.Add(nevaRadio, flag=wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(printersSizer)

		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("The Cura by Dagoma software is now ready to use with your 3D printer.")))
		sizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Feel free to contact us!"), URL=contact_url))
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Enjoy!")))

		self.SetSizerAndFit(sizer)

	def OnDiscoEasy200Select(self, e):
		profile.putPreference('xml_file', "discoeasy200.xml")

	def OnNevaSelect(self, e):
		profile.putPreference('xml_file', "neva.xml")

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
