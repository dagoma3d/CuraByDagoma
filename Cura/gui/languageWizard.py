#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2016 Aurelien Gibaud - Released under terms of the AGPLv3 License"

import os
import webbrowser
import threading
import time
import math

import platform

import wx
import wx.wizard
import wx.lib.hyperlink as hl

from Cura.gui import firmwareInstall
from Cura.gui import printWindow
from Cura.util import machineCom
from Cura.util import profile
from Cura.util import gcodeGenerator
from Cura.util import resources

from Cura.util import resources
from xml.dom import minidom

doc = minidom.parse(resources.getPathForXML('xml_config.xml'))

def getNodeText(node):
	nodelist = node.childNodes
	result = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			result.append(node.data)
	return ''.join(result)


class InfoBox(wx.Panel):
	def __init__(self, parent):
		super(InfoBox, self).__init__(parent)
		self.SetBackgroundColour('#FFFF80')

		self.sizer = wx.GridBagSizer(5, 5)
		self.SetSizer(self.sizer)

		self.attentionBitmap = wx.Bitmap(resources.getPathForImage('attention.png'))
		self.errorBitmap = wx.Bitmap(resources.getPathForImage('error.png'))
		self.readyBitmap = wx.Bitmap(resources.getPathForImage('ready.png'))
		self.busyBitmap = [
			wx.Bitmap(resources.getPathForImage('busy-0.png')),
			wx.Bitmap(resources.getPathForImage('busy-1.png')),
			wx.Bitmap(resources.getPathForImage('busy-2.png')),
			wx.Bitmap(resources.getPathForImage('busy-3.png'))
		]

		self.bitmap = wx.StaticBitmap(self, -1, wx.EmptyBitmapRGBA(24, 24, red=255, green=255, blue=255, alpha=1))
		self.text = wx.StaticText(self, -1, '')
		self.extraInfoButton = wx.Button(self, -1, 'i', style=wx.BU_EXACTFIT)
		self.sizer.Add(self.bitmap, pos=(0, 0), flag=wx.ALL, border=5)
		self.sizer.Add(self.text, pos=(0, 1), flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.Add(self.extraInfoButton, pos=(0,2), flag=wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.AddGrowableCol(1)

		self.extraInfoButton.Show(False)

		self.extraInfoUrl = ''
		self.busyState = None
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.doBusyUpdate, self.timer)
		self.Bind(wx.EVT_BUTTON, self.doExtraInfo, self.extraInfoButton)
		self.timer.Start(100)

	def SetInfo(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.Refresh()

	def SetError(self, info, extraInfoUrl):
		self.extraInfoUrl = extraInfoUrl
		self.SetBackgroundColour('#FF8080')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(True)
		self.Layout()
		self.SetErrorIndicator()
		self.Refresh()

	def SetAttention(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.SetAttentionIndicator()
		self.Layout()
		self.Refresh()

	def SetBusy(self, info):
		self.SetInfo(info)
		self.SetBusyIndicator()

	def SetBusyIndicator(self):
		self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def doExtraInfo(self, e):
		webbrowser.open(self.extraInfoUrl)

	def doBusyUpdate(self, e):
		if self.busyState is None:
			return
		self.busyState += 1
		if self.busyState >= len(self.busyBitmap):
			self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def SetReadyIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.readyBitmap)

	def SetErrorIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.errorBitmap)

	def SetAttentionIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.attentionBitmap)

class InfoPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent, title):
		wx.wizard.WizardPageSimple.__init__(self, parent)

		sizer = wx.GridBagSizer(5, 5)
		self.sizer = sizer
		self.SetSizer(sizer)

		title = wx.StaticText(self, -1, title)
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		sizer.Add(title, pos=(0, 0), span=(1, 2), flag=wx.ALIGN_CENTRE | wx.ALL)
		sizer.Add(wx.StaticLine(self, -1), pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		sizer.AddGrowableCol(1)

		self.rowNr = 2

	def AddText(self, info):
		text = wx.StaticText(self, -1, info)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return text

	def AddSeperator(self):
		self.GetSizer().Add(wx.StaticLine(self, -1), pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1

	def AddHiddenSeperator(self):
		self.AddText("")

	def AddInfoBox(self):
		infoBox = InfoBox(self)
		self.GetSizer().Add(infoBox, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
		self.rowNr += 1
		return infoBox

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

class LanguageSelectPage(InfoPage):
	def __init__(self, parent):
		page = doc.getElementsByTagName("LanguageSelectPage")[0]

		super(LanguageSelectPage, self).__init__(parent, _(page.getAttribute("title")))
		self.AddText(_(getNodeText(page.getElementsByTagName("Line1")[0])))

		self.FrRadio = self.AddRadioButton("Français".decode("utf-8"))
		#self.FrRadio = self.AddRadioButton(_("French"))
		#self.FrRadio.Bind(wx.EVT_RADIOBUTTON, self.OnSelectFr)

		self.EnRadio = self.AddRadioButton("English")
		#self.EnRadio = self.AddRadioButton(_("English"))
		#self.EnRadio.Bind(wx.EVT_RADIOBUTTON, self.OnSelectEn)

		default_language = 'English'
		default_locale = "en_US"
		if platform.system() == "Darwin":
			import commands
			data = commands.getoutput("locale")
			data = data.split("\n")
			for data_item in data:
				# Find the language locale
			  	if data_item.split("=")[0] == "LANG":
				  	self.AddText(data_item.decode("utf-8"))
			    	default_locale = data_item.split("=")[1].split(".")[0]

					import locale
					if locale.getdefaultlocale()[0] is None:
						self.AddText("Default locale = None")
					else:
						self.AddText(locale.getdefaultlocale()[0].decode("utf-8"))
		else:
			import locale
			default_locale = locale.getdefaultlocale()[0]

		if not default_locale.find('fr') == -1:
			self.FrRadio.SetValue(True)
		else:
			self.EnRadio.SetValue(True)

	def StoreData(self):
		if self.FrRadio.GetValue():
			profile.putPreference('language', 'French')

		if self.EnRadio.GetValue():
			profile.putPreference('language', 'English')

		from Cura.util import resources
		resources.setupLocalization(profile.getPreference('language'))  # it's important to set up localization at very beginning to install _

	#def OnSelectFr(self, e):
	#	wx.wizard.WizardPageSimple.Chain(self, self.GetParent().machineSelectPage)

	#def OnSelectEn(self, e):
	#	wx.wizard.WizardPageSimple.Chain(self, self.GetParent().machineSelectPage)

	def AllowBack(self):
		return False

	def AllowNext(self):
	#	wx.wizard.WizardPageSimple.Chain(self, self.GetParent().machineSelectPage)
		return True

class languageWizard(wx.wizard.Wizard):
	def __init__(self, addNew = False):
		super(languageWizard, self).__init__(None, -1, _("Assistant de configuration"))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.languageSelectPage = LanguageSelectPage(self)

		self.FitToPage(self.languageSelectPage)
		self.GetPageAreaSizer().Add(self.languageSelectPage)
		self.RunWizard(self.languageSelectPage)
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
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()
