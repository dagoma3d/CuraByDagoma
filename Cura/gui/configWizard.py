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

		self.name = profile.getMachineSetting('machine_name')
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
		printers = resources.getPrinters()
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
				self.name = printer.get('name')
			else:
				if printer.get('name') == self.name:
					radio.SetValue(True)
				else:
					radio.SetValue(False)

			def OnPrinterSelect(e, name = printer.get('name')):
				self.name = name

				self.GetParent().optionsPanel.UpdateDisplay(name)

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

		self.disco_addons_printers = ['DiscoEasy200', 'DiscoUltimate']
		self.multinozzle_printers = ['Sigma']
		if profile.getPreferenceBool('show_magis_options'):
			self.multinozzle_printers.append('Magis')
		self.with_options_printers = self.disco_addons_printers + self.multinozzle_printers

		self.extruder_amount = profile.getMachineSettingInt('extruder_amount')
		self.machine_width = profile.getMachineSettingFloat('machine_width')
		self.nozzle_size = profile.getMachineSettingFloat('nozzle_size')

		self.oSizer = wx.FlexGridSizer(3, 2, 0, 0)

		self.dualExtrusionChoiceLabel = wx.StaticText(self, wx.ID_ANY, _('Dual extrusion :') + ' ')
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.dualExtrusionChoice = wx.Choice(self, wx.ID_ANY, size = (100, -1), choices = [_('Yes'), _('No')])
		else:
			self.dualExtrusionChoice = wx.ComboBox(self, wx.ID_ANY, size = (100, -1), choices = [_('Yes'), _('No')] , style=wx.CB_DROPDOWN | wx.CB_READONLY)
		if self.extruder_amount == 1:
			self.dualExtrusionChoice.SetSelection(1)
		else:
			self.dualExtrusionChoice.SetSelection(0)
		
		self.xlChoiceLabel = wx.StaticText(self, wx.ID_ANY, _('XL addon :') + ' ')
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.xlChoice = wx.Choice(self, wx.ID_ANY, size = (100, -1), choices = [_('Yes'), _('No')])
		else:
			self.xlChoice = wx.ComboBox(self, wx.ID_ANY, size = (100, -1), choices = [_('Yes'), _('No')] , style=wx.CB_DROPDOWN | wx.CB_READONLY)
		if self.machine_width > 205:
			self.xlChoice.SetSelection(0)
		else:
			self.xlChoice.SetSelection(1)

		self.nozzleSizeChoiceLabel = wx.StaticText(self, wx.ID_ANY, _('Nozzle size :') + ' ')
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			#self.nozzleSizeChoice = wx.Choice(self, wx.ID_ANY, size = (100, -1), choices = [_('0.4 mm'), _('0.8 mm'), _('0.6 mm')])
			self.nozzleSizeChoice = wx.Choice(self, wx.ID_ANY, size = (100, -1), choices = [_('0.4 mm'), _('0.8 mm')])
		else:
			#self.nozzleSizeChoice = wx.ComboBox(self, wx.ID_ANY, size = (100, -1), choices = [_('0.4 mm'), _('0.8 mm'), _('0.6 mm')] , style=wx.CB_DROPDOWN | wx.CB_READONLY)
			self.nozzleSizeChoice = wx.ComboBox(self, wx.ID_ANY, size = (100, -1), choices = [_('0.4 mm'), _('0.8 mm')] , style=wx.CB_DROPDOWN | wx.CB_READONLY)

		if self.nozzle_size == 0.6:
			self.nozzleSizeChoice.SetSelection(2)
		elif self.nozzle_size == 0.8:
			self.nozzleSizeChoice.SetSelection(1)
		else:
			self.nozzleSizeChoice.SetSelection(0)

		self.oSizer.Add(self.dualExtrusionChoiceLabel)
		self.oSizer.Add(self.dualExtrusionChoice)
		self.oSizer.Add(self.xlChoiceLabel)
		self.oSizer.Add(self.xlChoice)
		self.oSizer.Add(self.nozzleSizeChoiceLabel)
		self.oSizer.Add(self.nozzleSizeChoice)

		if sys.platform == 'darwin':
			self.Bind(wx.EVT_CHOICE, self.OnDualExtrusionChanged, self.dualExtrusionChoice)
			self.Bind(wx.EVT_CHOICE, self.OnXlChanged, self.xlChoice)
			self.Bind(wx.EVT_CHOICE, self.OnNozzleSizeChanged, self.nozzleSizeChoice)
		else:
			self.Bind(wx.EVT_COMBOBOX, self.OnDualExtrusionChanged, self.dualExtrusionChoice)
			self.Bind(wx.EVT_COMBOBOX, self.OnXlChanged, self.xlChoice)
			self.Bind(wx.EVT_COMBOBOX, self.OnNozzleSizeChanged, self.nozzleSizeChoice)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Which option(s) do you use?")), flag=wx.BOTTOM, border=5)
		sizer.Add(self.oSizer)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(sizer)
		self.Layout()

	def OnDualExtrusionChanged(self, event):
		if self.dualExtrusionChoice.GetSelection() == 0:
			self.extruder_amount = '2'
		else:
			self.extruder_amount = '1'
		event.Skip()
	
	def OnXlChanged(self, event):
		if self.xlChoice.GetSelection() == 0:
			self.machine_width = 298
		else:
			self.machine_width = 205
		event.Skip()

	def OnNozzleSizeChanged(self, event):
		if self.nozzleSizeChoice.GetSelection() == 2:
			self.nozzle_size = 0.6
		elif self.nozzleSizeChoice.GetSelection() == 1:
			self.nozzle_size = 0.8
		else:
			self.nozzle_size = 0.4
		event.Skip()

	def UpdateDisplay(self, name):
		self.Show(name in self.with_options_printers)
		self.dualExtrusionChoiceLabel.Show(name in self.disco_addons_printers)
		self.dualExtrusionChoice.Show(name in self.disco_addons_printers)
		self.xlChoiceLabel.Show(name in self.disco_addons_printers)
		self.xlChoice.Show(name in self.disco_addons_printers)
		self.nozzleSizeChoiceLabel.Show(name in self.multinozzle_printers)
		self.nozzleSizeChoice.Show(name in self.multinozzle_printers)
		self.GetParent().Layout()
		self.GetParent().Fit()

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
		sizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Feel free to contact us!"), URL = _("contact_url")))
		sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Enjoy!")))

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
		self.printersPanel = PrintersPanel(self, firstTime)
		self.optionsPanel = OptionsPanel(self)
		if firstTime:
			welcomePanel = WelcomePanel(self)

		# Main sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(titlePanel, flag=wx.EXPAND)
		sizer.Add(self.printersPanel, flag=wx.EXPAND)
		sizer.Add(self.optionsPanel, flag=wx.EXPAND)
		if firstTime:
			sizer.Add(welcomePanel, flag=wx.EXPAND)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(sizer)
		self.Layout()

		self.optionsPanel.UpdateDisplay(self.printersPanel.name)

	def AllowNext(self):
		return True

	def AllowBack(self):
		return False

class ConfigWizard(wx.wizard.Wizard):
	def __init__(self, parent = None, firstTime = True):
		super(ConfigWizard, self).__init__(parent, -1, _("Configuration wizard"))

		self.parent = parent
		if firstTime:
			profile.putPreference('xml_file', 'discovery200.xml')

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.OnPageFinished)

		self.configurationPage = ConfigurationPage(self, firstTime)

		#self.FitToPage(self.configurationPage)
		self.GetPageAreaSizer().Add(self.configurationPage)
		self.RunWizard(self.configurationPage)
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
		disco_addons_printers = self.configurationPage.optionsPanel.disco_addons_printers
		multinozzle_printers = self.configurationPage.optionsPanel.multinozzle_printers
		name = self.configurationPage.printersPanel.name
		extruder_amount = self.configurationPage.optionsPanel.extruder_amount
		machine_width = self.configurationPage.optionsPanel.machine_width
		nozzle_size = self.configurationPage.optionsPanel.nozzle_size

		if name in disco_addons_printers:
			machine_width = 205 if machine_width < 205 else machine_width
		profile.putMachineSetting('machine_width', machine_width)

		xml_file = name.lower() + '.xml'
		if name in multinozzle_printers and not nozzle_size == 0.4:
			xml_file = name.lower() + '_' + str(nozzle_size) + '.xml'
		if name in disco_addons_printers and int(extruder_amount) == 2:
			xml_file = name.lower() + '_dual.xml'
		profile.putPreference('xml_file', xml_file)

		if self.parent is not None:
			self.parent.ReloadSettingPanels()
