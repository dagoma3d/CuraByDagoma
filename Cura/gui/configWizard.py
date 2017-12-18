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

from xml.dom import minidom

doc = minidom.parse(resources.getPathForXML('xml_config.xml'))

class InfoPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent, title):
		wx.wizard.WizardPageSimple.__init__(self, parent)

		sizer = wx.GridBagSizer(5, 5)
		self.sizer = sizer
		self.SetSizer(sizer)

		title = wx.StaticText(self, -1, title)
		title.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
		sizer.Add(title, pos=(0, 0), span=(1, 2), flag=wx.ALIGN_CENTRE | wx.ALL)
		sizer.Add(wx.StaticLine(self, -1), pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		sizer.AddGrowableCol(1)

		self.rowNr = 2

	def AddText(self, info):
		text = wx.StaticText(self, -1, info)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return text

	def AddLink(self, info):
		language = profile.getPreference('language')
		if language == "French":
			url = "https://dagoma.fr/heroes/diagnostique-en-ligne.html"
		else:
			url = "https://dagoma3d.com/pages/contact-us"
		link = hl.HyperLinkCtrl(self, wx.ID_ANY, info, URL=url)
		self.GetSizer().Add(link, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return link

	def AddSeperator(self):
		self.GetSizer().Add(wx.StaticLine(self, -1), pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1

	def AddHiddenSeperator(self):
		self.AddText("")

	def AddRadioButton(self, label, style=0):
		radio = wx.RadioButton(self, -1, label, style=style)
		self.GetSizer().Add(radio, pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1
		return radio

	def AddCheckbox(self, label, checked=False):
		check = wx.CheckBox(self, -1)
		text = wx.StaticText(self, -1, label)
		check.SetValue(checked)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 2), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AddButton(self, label):
		button = wx.Button(self, -1, label)
		self.GetSizer().Add(button, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return button

	def AddDualButton(self, label1, label2):
		button1 = wx.Button(self, -1, label1)
		self.GetSizer().Add(button1, pos=(self.rowNr, 0), flag=wx.RIGHT)
		button2 = wx.Button(self, -1, label2)
		self.GetSizer().Add(button2, pos=(self.rowNr, 1))
		self.rowNr += 1
		return button1, button2

	def AddTextCtrl(self, value):
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(ret, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddLabelTextCtrl(self, info, value):
		text = wx.StaticText(self, -1, info)
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(ret, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddTextCtrlButton(self, value, buttonText):
		text = wx.TextCtrl(self, -1, value)
		button = wx.Button(self, -1, buttonText)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(button, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return text, button

	def AddBitmap(self, bitmap):
		bitmap = wx.StaticBitmap(self, -1, bitmap)
		self.GetSizer().Add(bitmap, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return bitmap

	def AddCheckmark(self, label, bitmap):
		check = wx.StaticBitmap(self, -1, bitmap)
		text = wx.StaticText(self, -1, label)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 1), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AllowNext(self):
		return True

	def AllowBack(self):
		return True

	def StoreData(self):
		pass

class ConfigurationPage(InfoPage):
	def __init__(self, parent):
		printername = doc.getElementsByTagName("Printer")[0].getElementsByTagName("machine_name")[0].childNodes[0].data
		super(ConfigurationPage, self).__init__(parent, _("Configuration Cura by Dagoma %s") % printername)
		self.AddText(_("Dagoma would like to thank you for your trust."))
		self.AddText(_("The Cura by Dagoma software is now ready to use with your %s 3D printer.") % printername)
		self.AddLink(_("Feel free to contact us!"))
		self.AddSeperator()
		self.AddText(_("Enjoy!"))

	def AllowNext(self):
		return True

	def AllowBack(self):
		return False

	def StoreData(self):
		def getNodeText(node):
			nodelist = node.childNodes
			result = []
			for node in nodelist:
				if node.nodeType == node.TEXT_NODE:
					result.append(node.data)
			return ''.join(result)

		def getxml_disco(doc, two):
			return getNodeText(doc.getElementsByTagName("Printer")[0].getElementsByTagName(two)[0])

		def setvalue_from_xml(variable, doc = doc):
			try:
				profile.putMachineSetting(variable, getxml_disco(doc, variable))
			except:
				pass

		profile.putProfileSetting('retraction_enable', 'True')
		profile.putPreference('submit_slice_information', 'False')
		profile.putProfileSetting('nozzle_size', getxml_disco(doc, 'nozzle_size'))
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSetting('nozzle_size')) * 2)

		setvalue_from_xml('machine_name')
		setvalue_from_xml('machine_type')
		setvalue_from_xml('machine_width')
		setvalue_from_xml('machine_depth')
		setvalue_from_xml('machine_height')
		setvalue_from_xml('extruder_amount')
		setvalue_from_xml('has_heated_bed')
		setvalue_from_xml('machine_center_is_zero')
		setvalue_from_xml('machine_shape')
		setvalue_from_xml('extruder_head_size_min_x')
		setvalue_from_xml('extruder_head_size_min_y')
		setvalue_from_xml('extruder_head_size_max_x')
		setvalue_from_xml('extruder_head_size_max_y')
		setvalue_from_xml('extruder_head_size_height')
		setvalue_from_xml('gcode_flavor')

		profile.checkAndUpdateMachineName()

class ConfigWizard(wx.wizard.Wizard):
	def __init__(self):
		super(ConfigWizard, self).__init__(None, -1, _("Configuration wizard"))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.configurationPage = ConfigurationPage(self)

		self.FitToPage(self.configurationPage)
		self.GetPageAreaSizer().Add(self.configurationPage)
		self.RunWizard(self.configurationPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

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
		if e.GetPage().AllowNext():
			next_btn.Enable()
		else:
			next_btn.Disable()
		if e.GetPage().AllowBack():
			prev_btn.Enable()
		else:
			prev_btn.Disable()
