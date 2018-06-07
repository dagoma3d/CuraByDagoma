#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import platform
import sys

import wx
import wx.wizard
import wx.lib.hyperlink as hl

from Cura.util import profile
from Cura.util import resources

#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import platform
import sys

import wx
import wx.wizard
import wx.lib.hyperlink as hl

from Cura.util import profile
from Cura.util import resources

class wxPrinter():
	def __init__(self, image = None, name = None, description = None):
		self.image = image
		self.name = name
		self.description = description

class PrintersPanel(wx.Panel):
	def __init__(self, parent, isWizard = False):
		wx.Panel.__init__(self, parent, wx.ID_ANY)

		printers = self.getPrinters(isWizard)

		pSizer = wx.FlexGridSizer(3, len(printers), 0, 0)
		pSizer.SetFlexibleDirection(wx.VERTICAL)
		for printer in printers:
			pSizer.Add(printer.image, flag=wx.ALIGN_CENTER)
		for printer in printers:
			pSizer.Add(printer.name, flag=wx.ALIGN_CENTER)
		for printer in printers:
			pSizer.Add(printer.description, flag=wx.ALIGN_CENTER)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Which printer do you use?")), flag=wx.BOTTOM, border=5)
		sizer.Add(pSizer)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(sizer)
		self.Layout()

	def getPrinters(self, isWizard):
		# Build printers array
		printers = resources.getPrinterOptions(profile.getPreference('internal_use'))
		wxPrinters = []
		firstItem = True
		for printer in printers:
			wx_printer = wxPrinter()
			img = wx.Image(resources.getPathForImage(printer.get('img')), wx.BITMAP_TYPE_ANY)
			wx_printer.image = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img))

			if firstItem:
				radio = wx.RadioButton(self, -1, printer.get('name'), style=wx.RB_GROUP)
			else:
				radio = wx.RadioButton(self, -1, printer.get('name'))

			if isWizard and firstItem:
				radio.SetValue(True)
				profile.putPreference('xml_file', printer.get('config'))
			else:
				if printer.get('config') == profile.getPreference('xml_file'):
					radio.SetValue(True)
				else:
					radio.SetValue(False)

			def OnPrinterSelect(e, config = printer.get('config'), name = printer.get('name')):
				profile.putPreference('xml_file', config)
				if name != 'DiscoEasy200':
					profile.putPreference('printerhead_index', '-1')
					profile.putMachineSetting('extruder_amount', '1')
					profile.putProfileSetting('wipe_tower', 'False')

				self.GetParent().optionsPanel.Show(name == 'DiscoEasy200')
				self.GetParent().Layout()
				self.GetParent().Fit()

			radio.Bind(wx.EVT_RADIOBUTTON, OnPrinterSelect)
			wx_printer.name = radio

			desc_text = printer.get('desc')
			if desc_text != '':
				desc_text = _(desc_text)
			desc = wx.StaticText(self, -1, desc_text)
			wx_printer.description = desc

			wxPrinters.append(wx_printer)

			firstItem = False

		return wxPrinters

class OptionsPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, wx.ID_ANY)

		oSizer = wx.FlexGridSizer(2, 2, 0, 0)
		oSizer.Add(wx.StaticText(self, wx.ID_ANY, _('Printhead version :') + ' '))
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.printerHeadChoice = wx.Choice(self, wx.ID_ANY, choices = [_('Standard printhead (v2)'), _('New printhead (v3)')])
		else:
			self.printerHeadChoice = wx.ComboBox(self, wx.ID_ANY, choices = [_('Standard printhead (v2)'), _('New printhead (v3)')] , style=wx.CB_DROPDOWN | wx.CB_READONLY)
		if int(profile.getPreference('printerhead_index')) == 1:
			self.printerHeadChoice.SetSelection(1)
		else:
			self.printerHeadChoice.SetSelection(0)
		oSizer.Add(self.printerHeadChoice)
		oSizer.Add(wx.StaticText(self, wx.ID_ANY, _('Dual extrusion :') + ' '))
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.dualExtrusionChoice = wx.Choice(self, wx.ID_ANY, choices = [_('Yes'), _('No')])
		else:
			self.dualExtrusionChoice = wx.ComboBox(self, wx.ID_ANY, choices = [_('Yes'), _('No')] , style=wx.CB_DROPDOWN | wx.CB_READONLY)
		if int(profile.getMachineSetting('extruder_amount')) == 1:
			self.dualExtrusionChoice.SetSelection(1)
		else:
			self.dualExtrusionChoice.SetSelection(0)
		oSizer.Add(self.dualExtrusionChoice)

		if sys.platform == 'darwin':
			self.Bind(wx.EVT_CHOICE, self.OnPrinterHeadChanged, self.printerHeadChoice)
			self.Bind(wx.EVT_CHOICE, self.OnDualExtrusionChanged, self.dualExtrusionChoice)
		else:
			self.Bind(wx.EVT_COMBOBOX, self.OnPrinterHeadChanged, self.printerHeadChoice)
			self.Bind(wx.EVT_COMBOBOX, self.OnDualExtrusionChanged, self.dualExtrusionChoice)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Which options do you use?")), flag=wx.BOTTOM, border=5)
		sizer.Add(oSizer)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(sizer)
		self.Layout()

	def OnPrinterHeadChanged(self, event):
		profile.putPreference('printerhead_index', str(self.printerHeadChoice.GetSelection()))
		event.Skip()

	def OnDualExtrusionChanged(self, event):
		if self.dualExtrusionChoice.GetSelection() == 0:
			profile.putMachineSetting('extruder_amount', '2')
			profile.putProfileSetting('wipe_tower', 'True')
		else:
			profile.putMachineSetting('extruder_amount', '1')
			profile.putProfileSetting('wipe_tower', 'False')
		event.Skip()

class TitlePanel(wx.Panel):
	def __init__(self, parent, title, subtitle = None):
		wx.Panel.__init__(self, parent, wx.ID_ANY)
		# Title
		title = wx.StaticText(self, wx.ID_ANY, title)
		title.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(title, flag=wx.ALIGN_CENTRE)
		if subtitle:
			sizer.Add(wx.StaticText(self, wx.ID_ANY, subtitle), flag=wx.ALIGN_CENTRE)

		self.SetAutoLayout(True)
		self.SetSizer(sizer)
		self.Layout()

class WelcomePanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, wx.ID_ANY)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("The Cura by Dagoma software is now ready to use with your 3D printer.")))
		sizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Feel free to contact us!"), URL = profile.getPreference('contact_url')))
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Enjoy!")))

		self.SetAutoLayout(True)
		self.SetSizer(sizer)
		self.Layout()

class ConfirmationPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, wx.ID_ANY)

		self.okButton = wx.Button(self, wx.ID_ANY, 'Ok')

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.okButton, flag=wx.ALIGN_RIGHT)

		self.SetAutoLayout(True)
		self.SetSizer(sizer)
		self.Layout()

class ConfigurationPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent, firstTime):
		wx.wizard.WizardPageSimple.__init__(self, parent)

		if firstTime:
			titlePanel = TitlePanel(self, _("Configuration Cura by Dagoma"), _("Dagoma would like to thank you for your trust."))
		else:
			titlePanel = TitlePanel(self, _("Configuration Cura by Dagoma"))
		printersPanel = PrintersPanel(self, firstTime)
		self.optionsPanel = OptionsPanel(self)
		if firstTime:
			welcomePanel = WelcomePanel(self)

		# Main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(titlePanel, flag=wx.EXPAND)
		sizer.Add(printersPanel, flag=wx.EXPAND)
		sizer.Add(self.optionsPanel, flag=wx.EXPAND)
		if firstTime:
			sizer.Add(welcomePanel, flag=wx.EXPAND)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(sizer)
		self.Layout()

		if profile.getMachineSetting('machine_name') != 'DiscoEasy200':
			self.optionsPanel.Hide()

	def AllowNext(self):
		return True

	def AllowBack(self):
		return False

class ConfigWizard(wx.wizard.Wizard):
	def __init__(self, parent = None, firstTime = True):
		super(ConfigWizard, self).__init__(parent, -1, _("Configuration wizard"))

		self.parent = parent

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.OnPageFinished)
		wx.EVT_CLOSE(self, self.OnClose)

		self.configurationPage = ConfigurationPage(self, firstTime)

		#self.FitToPage(self.configurationPage)
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
			next_btn.SetLabel('Ok')
			cancel_btn.Disable()
			cancel_btn.Hide()
		if e.GetPage().AllowNext():
			next_btn.Enable()
		else:
			next_btn.Disable()
			next_btn.Hide()
		if e.GetPage().AllowBack():
			prev_btn.Enable()
		else:
			prev_btn.Disable()
			prev_btn.Hide()

	def OnPageFinished(self, e):
		print "Configuration wizard finished..."
		if self.parent is not None:
			self.parent.ReloadSettingPanels()

	def OnClose(self, e):
		print "Configuration wizard finished..."
		if self.parent is not None:
			self.parent.ReloadSettingPanels()
		self.Destroy()
