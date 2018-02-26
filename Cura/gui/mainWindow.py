#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import platform
import wx
import os
import webbrowser
import sys
import wx.lib.hyperlink as hl
from wx.lib import scrolledpanel

from Cura.gui import configBase
from Cura.gui import pausePluginPanel
from Cura.gui import configWizard
from Cura.gui import sceneView
from Cura.gui import aboutWindow
from Cura.gui import printerWindow
from Cura.gui.util import dropTarget
from Cura.gui.tools import pidDebugger
from Cura.util import profile
from Cura.util import version
from Cura.util import meshLoader
from Cura.util import resources
from xml.dom import minidom

class mainWindow(wx.Frame):
	def __init__(self):
		cbdVersion = profile.getPreference('cbd_version')
		windowTitle = 'Cura by Dagoma ' + cbdVersion
		super(mainWindow, self).__init__(None, title=windowTitle, pos=(0, 0), size=wx.DisplaySize())

		wx.EVT_CLOSE(self, self.OnClose)

		# allow dropping any file, restrict later
		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles))

		frameIcon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameIcon)

		# TODO: wxWidgets 2.9.4 has a bug when NSView does not register for dragged types when wx drop target is set. It was fixed in 2.9.5
		if sys.platform.startswith('darwin'):
			try:
				import objc
				nsWindow = objc.objc_object(c_void_p=self.MacGetTopLevelWindowRef())
				view = nsWindow.contentView()
				view.registerForDraggedTypes_([u'NSFilenamesPboardType'])
			except:
				pass

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(localFilename=mruFile, style=wx.CONFIG_USE_LOCAL_FILE)

		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in xrange(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in xrange(10)]
		self.profileFileHistory = wx.FileHistory(10, self.ID_MRU_PROFILE1)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Load(self.config)

		self.statusBar = self.CreateStatusBar()

		self.menuBar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(wx.ID_OPEN, _("Open an Object") + "\tCTRL+O", _("Open a 3d object file."))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showLoadModel(), i)
		i = self.fileMenu.Append(wx.ID_SAVEAS, _("Save the build plate") + "\tCTRL+S", _("Save the current build plate as a stl file."))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveModel(), i)
		i = self.fileMenu.Append(wx.ID_SAVE, _("Prepare the Print") + "\tCTRL+P", _("Save the generated gcode on a sd card or on your computer."))
		self.Bind(wx.EVT_MENU, self.OnPreparePrint, i)

		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendSubMenu(modelHistoryMenu, '&' + _("Recently Opened Objects"))
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, _("Quit"), _("Exit the application."))
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menuBar.Append(self.fileMenu, _("File"))

		self.settingsMenu = wx.Menu()
		self.languagesMenu = wx.Menu()
		for language in resources.getLanguageOptions():
			i = self.languagesMenu.Append(-1, _(language[1]), _('You have to reopen the application to load the correct language.'), wx.ITEM_RADIO)
			if profile.getPreference('language') == language[1]:
				i.Check(True)
			else:
				i.Check(False)
			def OnLanguageSelect(e, selected_language=language[1]):
				profile.putPreference('language', selected_language)
			self.Bind(wx.EVT_MENU, OnLanguageSelect, i)
		self.settingsMenu.AppendSubMenu(self.languagesMenu, _("Language"))
		i = self.settingsMenu.Append(wx.ID_ANY, _("Printer"), _("Choose the printer you want to use."))
		self.Bind(wx.EVT_MENU, self.OnPrinterWindow, i)
		self.menuBar.Append(self.settingsMenu, _("Preferences"))

		contactUrl = profile.getPreference('contact_url')
		buyUrl = profile.getPreference('buy_url')
		self.helpMenu = wx.Menu()
		i = self.helpMenu.Append(wx.ID_ANY, _("Contact us"), _("Contact us for any further information."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(contactUrl), i)
		i = self.helpMenu.Append(wx.ID_ANY, _("Buy filament"), _("Buy filament on our website."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(buyUrl), i)
		i = self.helpMenu.Append(wx.ID_ABOUT, _("About"), _("Display all components used to build this application."))
		self.Bind(wx.EVT_MENU, self.OnAbout, i)
		self.menuBar.Append(self.helpMenu, _("Help"))

		self.SetMenuBar(self.menuBar)

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3DSASH | wx.SP_LIVE_UPDATE)
		self.splitter.SetMinimumPaneSize(profile.getPreferenceInt('minimum_pane_size'))
		self.splitter.SetSashGravity(1.0) # Only the SceneView is resized when the windows size is modifed
		self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		self.viewPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		#self.optionsPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.optionsPane = scrolledpanel.ScrolledPanel(self.splitter, style=wx.BORDER_NONE)
		self.optionsPane.SetupScrolling(True, True)

		##Gui components##
		self.normalSettingsPanel = normalSettingsPanel(self.optionsPane, lambda : self.scene.sceneUpdated())

		self.optionsSizer = wx.BoxSizer(wx.VERTICAL)
		self.optionsSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.optionsPane.SetSizerAndFit(self.optionsSizer)

		#Preview window
		self.scene = sceneView.SceneView(self.viewPane)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.viewPane.SetSizerAndFit(sizer)
		sizer.Add(self.scene, 1, flag=wx.EXPAND)

		self.splitter.SplitVertically(self.viewPane, self.optionsPane, profile.getPreferenceInt('window_normal_sash'))

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		self.SetSizerAndFit(sizer)
		sizer.Layout()

		self.UpdateProfileToAllControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		self.normalSettingsPanel.Show()

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2, wx.Display().GetClientArea().GetHeight()/2))
		self.SetMinSize((800, 600))
		self.Centre()
		self.Maximize(True)

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800, 600))
			self.Centre()

		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()
		self.scene.SetFocus()

	def OnPreparePrint(self, e):
		profile.printSlicingInfo()
		self.scene.OnPrintButton(1)
		e.Skip()

	def OnDropFiles(self, files):
		if len(files) > 0:
			self.UpdateProfileToAllControls()
		self.scene.loadFiles(files)

	def AddToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()

	def AddToModelMRU(self, file):
		self.modelFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()

	def OnProfileMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_PROFILE1
		path = self.profileFileHistory.GetHistoryFile(fileNum)
		# Update Profile MRU
		self.profileFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()
		# Load Profile
		profile.loadProfile(path)
		self.UpdateProfileToAllControls()

	def OnModelMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_MODEL1
		path = self.modelFileHistory.GetHistoryFile(fileNum)
		# Update Model MRU
		self.modelFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
		# Load Model
		profile.putPreference('lastFile', path)
		filelist = [ path ]
		self.scene.loadFiles(filelist)

	def UpdateProfileToAllControls(self):
		self.scene.OnViewChange()
		self.scene.sceneUpdated()
		if len(self.scene._scene.objects()) > 0:
			self.normalSettingsPanel.pausePluginButton.Enable()
		self.scene.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()

	def ReloadSettingPanels(self):
		self.optionsSizer.Detach(self.normalSettingsPanel)
		self.normalSettingsPanel.Destroy()
		self.normalSettingsPanel = normalSettingsPanel(self.optionsPane, lambda : self.scene.sceneUpdated())
		self.optionsSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.optionsPane.SetSizerAndFit(self.optionsSizer)
		self.UpdateProfileToAllControls()

	def OnPrinterWindow(self, e):
		printerBox = printerWindow.printerWindow(self)
		printerBox.Centre()
		printerBox.Show()

	def OnAbout(self, e):
		aboutBox = aboutWindow.aboutWindow(self)
		aboutBox.Centre()
		aboutBox.Show()

	def OnClose(self, e):
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		profile.putPreference('window_normal_sash', int('-' + str(self.optionsPane.GetSize()[0])))

		#HACK: Set the paint function of the glCanvas to nothing so it won't keep refreshing. Which can keep wxWidgets from quiting.
		print "Closing down"
		self.scene.OnPaint = lambda e : e
		self.scene._engine.cleanup()
		self.Destroy()

	def OnQuit(self, e):
		self.Close()

class normalSettingsPanel(configBase.configPanelBase):

	"Main user interface window"
	class Filament:
		def __init__(self):
			self.type = ''
			self.grip_temperature = '185'
			self.print_temperature = '185'
			self.filament_diameter = '1.74'
			self.filament_flow = '80'
			self.retraction_speed = '50'
			self.retraction_amount = '3.5'
			self.filament_physical_density = '1270'
			self.filament_cost_kg = '46'
			self.model_colour = '#FF9B00'
			self.layer_height = None
			self.solid_layer_thickness = None
			self.wall_thickness = None
			self.print_speed = None
			self.temp_preci = '0'
			self.travel_speed = None
			self.bottom_layer_speed = None
			self.infill_speed = None
			self.inset0_speed = None
			self.insetx_speed = None

	class Color:
		def __init__(self):
			self.label = ''
			self.name = ''

	class Filling:
		def __init__(self):
			self.type = ''
			self.fill_density = ''
			self.spiralize = ''

	class Precision:
		def __init__(self):
			self.type = ''
			self.layer_height = ''
			self.solid_layer_thickness = ''
			self.wall_thickness = ''
			self.print_speed = ''
			self.temp_preci = ''
			self.travel_speed = ''
			self.bottom_layer_speed = ''
			self.infill_speed = ''
			self.inset0_speed = ''
			self.insetx_speed = ''

	class PrinterHead:
		def __init__(self):
			self.type = ''
			self.fan_speed = ''
			self.cool_min_layer_time = ''

	class Support:
		def __init__(self):
			self.support = None

	class Adhesion:
		def __init__(self, platform_adhesion = 'None'):
			self.platform_adhesion = platform_adhesion

	class PrintingSurface:
		def __init__(self):
			self.name = ''
			self.height = ''

	class Offset:
		def __init__(self):
			self.value = ''
			self.input = ''

	class Sensor:
		def __init__(self, sensor='Enabled'):
			self.sensor = sensor

	def __init__(self, parent, callback = None):
		super(normalSettingsPanel, self).__init__(parent, callback)
		self.alreadyLoaded = False
		self.parent = parent
		self.loadConfiguration()
		self.warningStaticText = wx.StaticText(self, wx.ID_ANY)
		warningStaticTextFont = self.warningStaticText.GetFont()
		warningStaticTextFont.SetPointSize(10)
		warningStaticTextFont.SetWeight(wx.FONTWEIGHT_BOLD)
		self.warningStaticText.SetFont(warningStaticTextFont)
		self.colorComboBox = wx.ComboBox(self, wx.ID_ANY, choices = [] , style=wx.CB_DROPDOWN | wx.CB_READONLY)

		self.temperatureText = wx.StaticText(self, wx.ID_ANY, _(("Temperature (°C) :").decode('utf-8')))
		self.temperatureSpinCtrl = wx.SpinCtrl(self, wx.ID_ANY, profile.getProfileSetting('print_temperature'), min=175, max=255, style=wx.SP_ARROW_KEYS | wx.TE_AUTO_URL)
		self.printButton = wx.Button(self, wx.ID_ANY, _("Prepare the Print"))

		self.offsetStaticText = wx.StaticText(self, wx.ID_ANY, _("Offset (mm) :"))
		self.offsetTextCtrl = wx.TextCtrl(self, -1, profile.getProfileSetting('offset_input'))

		# Pause plugin
		self.pausePluginButton = wx.Button(self, wx.ID_ANY, _(("Color change(s)")))
		self.pausePluginPanel = pausePluginPanel.pausePluginPanel(self, callback)
		self.__setProperties()
		self.__doLayout()

		self.RefreshSupport()
		self.RefreshPrecision()
		self.RefreshPrinterHead()
		self.RefreshFilament()
		self.RefreshColor()
		self.RefreshTemperatureSpinCtrl()
		self.RefreshFilling()
		self.RefreshSensor()
		self.RefreshPrintingSurface()
		self.RefreshOffset()
		self.RefreshAdhesion()

		profile.saveProfile(profile.getDefaultProfilePath(), True)

		if sys.platform == 'darwin':
			self.Bind(wx.EVT_CHOICE, self.OnFilamentComboBoxChanged, self.filamentComboBox)
			self.Bind(wx.EVT_CHOICE, self.OnColorComboBoxChanged, self.colorComboBox)
		else:
			self.Bind(wx.EVT_COMBOBOX, self.OnFilamentComboBoxChanged, self.filamentComboBox)
			self.Bind(wx.EVT_COMBOBOX, self.OnColorComboBoxChanged, self.colorComboBox)

		self.Bind(wx.EVT_TEXT, self.OnTemperatureSpinCtrlChanged, self.temperatureSpinCtrl)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnTemperatureSpinCtrlChanged, self.temperatureSpinCtrl)
		self.Bind(wx.EVT_SPINCTRL, self.OnTemperatureSpinCtrlChanged, self.temperatureSpinCtrl)
		self.Bind(wx.EVT_RADIOBOX, self.OnPrecisionRadioBoxChanged, self.precisionRadioBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnPrinterHeadRadioBoxChanged, self.printerHeadRadioBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnSupportRadioBoxChanged, self.supportRadioBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnFillingRadioBoxChanged, self.fillingRadioBox)
		self.Bind(wx.EVT_CHECKBOX, self.OnSensorCheckBoxChanged,self.sensorCheckBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnPrintingSurfaceRadioBoxChanged, self.printingSurfaceRadioBox)
		self.Bind(wx.EVT_TEXT, self.OnOffsetTextCtrlChanged, self.offsetTextCtrl)
		self.Bind(wx.EVT_CHECKBOX, self.OnAdhesionCheckBoxChanged, self.adhesionCheckBox)
		self.Bind(wx.EVT_BUTTON, self.OnPreparePrintButtonClick, self.printButton)
		self.Bind(wx.EVT_BUTTON, self.OnPauseButtonClick, self.pausePluginButton)

	def __setProperties(self):
		self.temperatureSpinCtrl.Enable(False)
		self.supportRadioBox.SetSelection(0)


	def __doLayout(self):
		printerName = profile.getMachineSetting('machine_name')
		self.pausePluginButton.Disable()
		self.printButton.Disable()

		buyUrl = profile.getPreference('buy_url')
		filamentSizer = wx.BoxSizer(wx.HORIZONTAL)
		filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, _("Filament")))
		filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, " ("))
		filamentSizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Buy filament"), URL=buyUrl))
		filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, "):"))

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainSizer.Add(filamentSizer)
		mainSizer.Add(self.filamentComboBox, flag=wx.EXPAND|wx.BOTTOM, border=2)
		mainSizer.Add(self.colorComboBox, flag=wx.EXPAND)
		mainSizer.Add(self.warningStaticText)
		mainSizer.Add(self.temperatureText)
		mainSizer.Add(self.temperatureSpinCtrl, flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(self.fillingRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(self.precisionRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		if printerName == "DiscoEasy200":
			mainSizer.Add(self.printerHeadRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		else:
			self.printerHeadRadioBox.Hide()
		mainSizer.Add(self.supportRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		if printerName == "DiscoVery200":
			mainSizer.Add(self.printingSurfaceRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
			mainSizer.Add(self.offsetStaticText, flag=wx.EXPAND)
			mainSizer.Add(self.offsetTextCtrl, flag=wx.EXPAND|wx.BOTTOM, border=5)
		else:
			self.printingSurfaceRadioBox.Hide()
			self.offsetStaticText.Hide()
			self.offsetTextCtrl.Hide()
		if printerName != "Neva":
			mainSizer.Add(self.sensorCheckBox)
		else:
			self.sensorCheckBox.Hide()
		mainSizer.Add(self.adhesionCheckBox, flag=wx.BOTTOM, border=5)
		mainSizer.Add(self.pausePluginButton, flag=wx.EXPAND)
		mainSizer.Add(self.pausePluginPanel, flag=wx.EXPAND)
		mainSizer.Add(self.printButton, flag=wx.EXPAND|wx.TOP, border=5)

		self.SetSizerAndFit(mainSizer)
		self.Layout()

	def loadConfiguration(self):
		xmlFile = profile.getPreference('xml_file')
		self.configuration = minidom.parse(resources.getPathForXML(xmlFile))
		self.initPrinter()
		self.initConfiguration()
		self.initGCode()
		self.initFilament()
		self.initFilling()
		self.initPrecision()
		self.initPrinterHead()
		self.initSupport()
		self.initAdhesion()
		self.initPrintingSurface()
		self.initSensor()

	def initPrinter(self):
		printer = self.configuration.getElementsByTagName('Printer')[0]
		for paramNode in printer.childNodes:
			if paramNode.nodeType == paramNode.ELEMENT_NODE:
				paramName = paramNode.nodeName
				paramValue = paramNode.firstChild.nodeValue
				if paramValue is not None:
					profile.putMachineSetting(paramName, paramValue)

	def initConfiguration(self):
		config = self.configuration.getElementsByTagName('Configuration')[0]
		for paramNode in config.childNodes:
			if paramNode.nodeType == paramNode.ELEMENT_NODE:
				paramName = paramNode.nodeName
				paramValue = paramNode.firstChild.nodeValue
				if paramValue is not None:
					profile.putProfileSetting(paramName, paramValue)

	def initGCode(self):
		gcode = self.configuration.getElementsByTagName("GCODE")[0]
		gcode_start = gcode.getElementsByTagName("Gstart")[0].firstChild.nodeValue
		profile.putAlterationSetting('start.gcode', gcode_start)

		gcode_end = gcode.getElementsByTagName("Gend")[0].firstChild.nodeValue
		profile.putAlterationSetting('end.gcode', gcode_end)

	def initFilament(self):
		filaments = self.configuration.getElementsByTagName('Filament')
		self.filaments = []
		choices = []
		for filament in filaments:
			if filament.hasAttributes():
				fila = self.Filament()
				name = filament.getAttribute("name")
				choices.append(_(name))
				fila.type = name
			try :
				if len(filament.getElementsByTagName("grip_temperature")) > 0 is not None:
					fila.grip_temperature = filament.getElementsByTagName("grip_temperature")[0].firstChild.nodeValue
				else:
					fila.grip_temperature = filament.getElementsByTagName("print_temperature")[0].firstChild.nodeValue
				fila.print_temperature = filament.getElementsByTagName("print_temperature")[0].firstChild.nodeValue
				fila.filament_diameter = filament.getElementsByTagName("filament_diameter")[0].firstChild.nodeValue
				fila.filament_flow = filament.getElementsByTagName("filament_flow")[0].firstChild.nodeValue
				fila.retraction_speed = filament.getElementsByTagName("retraction_speed")[0].firstChild.nodeValue
				fila.retraction_amount = filament.getElementsByTagName("retraction_amount")[0].firstChild.nodeValue
				fila.filament_physical_density = filament.getElementsByTagName("filament_physical_density")[0].firstChild.nodeValue
				fila.filament_cost_kg = filament.getElementsByTagName("filament_cost_kg")[0].firstChild.nodeValue
				model_colour_tags = filament.getElementsByTagName("model_colour")
				if len(model_colour_tags) > 0:
					fila.model_colour = model_colour_tags[0].firstChild.nodeValue
				filament_type = fila.type.lower()
				if 'wood' in filament_type or 'flex' in filament_type:
					fila.layer_height = filament.getElementsByTagName("layer_height")[0].firstChild.nodeValue
					fila.solid_layer_thickness = filament.getElementsByTagName("solid_layer_thickness")[0].firstChild.nodeValue
					fila.wall_thickness = filament.getElementsByTagName("wall_thickness")[0].firstChild.nodeValue
					fila.print_speed = filament.getElementsByTagName("print_speed")[0].firstChild.nodeValue
					fila.travel_speed = filament.getElementsByTagName("travel_speed")[0].firstChild.nodeValue
					fila.bottom_layer_speed = filament.getElementsByTagName("bottom_layer_speed")[0].firstChild.nodeValue
					fila.infill_speed = filament.getElementsByTagName("infill_speed")[0].firstChild.nodeValue
					fila.inset0_speed = filament.getElementsByTagName("inset0_speed")[0].firstChild.nodeValue
					fila.insetx_speed = filament.getElementsByTagName("insetx_speed")[0].firstChild.nodeValue
				self.filaments.append(fila)
			except:
				print 'Some Error in Filament Bloc'
				pass

		self.filamentComboBox = wx.ComboBox(self, wx.ID_ANY, choices = choices , style=wx.CB_DROPDOWN | wx.CB_READONLY)
		self.filamentComboBox.SetSelection(int(profile.getPreference('filament_index')))

	def initFilling(self):
		fillings = self.configuration.getElementsByTagName("Filling")
		choices = []
		self.fillings = []
		for filling in fillings:
			if filling.hasAttributes():
				new_filling = self.Filling()
				name = _(filling.getAttribute("name"))
				choices.append(name)
				new_filling.type = name
				try :
					fill_density_tags = filling.getElementsByTagName("fill_density")
					if len(fill_density_tags) > 0:
						new_filling.fill_density = fill_density_tags[0].firstChild.nodeValue
					else:
						new_filling.fill_density = '0'
					spiralize_tags = filling.getElementsByTagName("spiralize")
					if len(spiralize_tags) > 0:
						new_filling.spiralize = spiralize_tags[0].firstChild.nodeValue
					else:
						new_filling.spiralize = 'False'
					self.fillings.append(new_filling)
				except:
					print 'Some Errors in Filling Bloc'
					pass
		self.fillingRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Filling density :"), choices = choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.fillingRadioBox.SetSelection(int(profile.getPreference('fill_index')))

	def initPrecision(self):
		precisions = self.configuration.getElementsByTagName("Precision")
		choices = []
		self.precisions = []
		for precision in precisions:
			if precision.hasAttributes():
				preci = self.Precision()
				name = precision.getAttribute("name")
				choices.append(_(name))
				preci.type = name
				try :
					preci.layer_height = precision.getElementsByTagName("layer_height")[0].firstChild.nodeValue
					preci.solid_layer_thickness = precision.getElementsByTagName("solid_layer_thickness")[0].firstChild.nodeValue
					preci.wall_thickness = precision.getElementsByTagName("wall_thickness")[0].firstChild.nodeValue
					preci.print_speed = precision.getElementsByTagName("print_speed")[0].firstChild.nodeValue
					preci.temp_preci = precision.getElementsByTagName("temp_preci")[0].firstChild.nodeValue
					preci.travel_speed = precision.getElementsByTagName("travel_speed")[0].firstChild.nodeValue
					preci.bottom_layer_speed = precision.getElementsByTagName("bottom_layer_speed")[0].firstChild.nodeValue
					preci.infill_speed = precision.getElementsByTagName("infill_speed")[0].firstChild.nodeValue
					preci.inset0_speed = precision.getElementsByTagName("inset0_speed")[0].firstChild.nodeValue
					preci.insetx_speed = precision.getElementsByTagName("insetx_speed")[0].firstChild.nodeValue
					self.precisions.append(preci)
				except :
					print 'Some Error in Precision Bloc'
					pass
		self.precisionRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Quality (layer thickness) :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.precisionRadioBox.SetSelection(int(profile.getPreference('precision_index')))

	def initPrinterHead(self):
		printerheads = self.configuration.getElementsByTagName("PrinterHead")
		choices = []
		self.heads = []
		for printerhead in printerheads:
			if printerhead.hasAttributes():
				new_printerhead = self.PrinterHead()
				name = printerhead.getAttribute("name")
				choices.append(_(name))
				new_printerhead.type = name
				try :
					new_printerhead.fan_speed = printerhead.getElementsByTagName("fan_speed")[0].firstChild.nodeValue
					new_printerhead.cool_min_layer_time = printerhead.getElementsByTagName("cool_min_layer_time")[0].firstChild.nodeValue
					self.heads.append(new_printerhead)
				except :
					print 'Some Error in PrinterHead Bloc'
					pass

		if len(choices) == 0:
			printerConfiguration = self.configuration.getElementsByTagName("Configuration")[0]
			name = "Standard printhead"
			choices.append(name)
			printhead = self.PrintingSurface()
			printhead.type = name
			printhead.fan_speed = printerConfiguration.getElementsByTagName("fan_speed")[0].firstChild.nodeValue
			printhead.cool_min_layer_time = printerConfiguration.getElementsByTagName("cool_min_layer_time")[0].firstChild.nodeValue
			self.heads.append(printhead)
			profile.putPreference('printerhead_index', '0')

		self.printerHeadRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Printhead version :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.printerHeadRadioBox.SetSelection(int(profile.getPreference('printerhead_index')))

	def initSupport(self):
		supports = [
			{'name': 'None', 'value': 'None'},
			{'name': 'Sides touching the build plate', 'value': 'Touching buildplate'},
			{'name': 'Everywhere (including holes)', 'value': 'Everywhere'}
		]
		choices = []
		self.supports = []
		for support in supports:
			supp = self.Support()
			name = _(support.get("name"))
			choices.append(name)
			supp.type = name
			try :
				supp.support = support.get("value")
				self.supports.append(supp)
			except :
				print 'Some Error in Supports Bloc'
				pass
		self.supportRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Printing supports :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

	def initAdhesion(self):
		self.adhesionCheckBox = wx.CheckBox(self, wx.ID_ANY, _("Improve the adhesion surface"))
		self.adhesions = []
		self.adhesions.append(self.Adhesion('Brim'))
		self.adhesions.append(self.Adhesion('None'))

	def initSensor(self):
		self.sensorCheckBox = wx.CheckBox(self, wx.ID_ANY, _("Use the sensor"))
		self.sensors = []
		self.sensors.append(self.Sensor('Enabled'))
		self.sensors.append(self.Sensor('Disabled'))

		isSensorEnabled = profile.getProfileSetting('sensor') == 'Enabled'
		self.sensorCheckBox.SetValue(isSensorEnabled)

	def initPrintingSurface(self):
		printing_surfaces = self.configuration.getElementsByTagName("PrintingSurface")
		choices = []
		self.printing_surfaces = []

		for printing_surface in printing_surfaces:
			if printing_surface.hasAttributes():
				prtsurf = self.PrintingSurface()
				name = printing_surface.getAttribute("name")
				choices.append(_(name))
				prtsurf.name = name
				try :
					prtsurf.height = printing_surface.getElementsByTagName("printing_surface_height")[0].firstChild.nodeValue
					self.printing_surfaces.append(prtsurf)
				except :
					print 'Some Error in Printing Surface Bloc'
					pass

		if len(choices) == 0:
			name = "Generic"
			choices.append(name)
			prtsurf = self.PrintingSurface()
			prtsurf.name = name
			prtsurf.height = 0.0
			self.printing_surfaces.append(prtsurf)

		self.printingSurfaceRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Printing surface :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.printingSurfaceRadioBox.SetStringSelection(profile.getProfileSetting('printing_surface_name'))

	def RefreshFilament(self):
		#print "Refresh fila"
		filament_index = self.filamentComboBox.GetSelection()
		fila = self.filaments[filament_index]
		profile.putPreference('filament_index', filament_index)
		profile.putPreference('filament_name', fila.type)
		profile.putProfileSetting('grip_temperature', fila.grip_temperature)
		calculated_print_temperature = float(fila.print_temperature)
		filament_type = fila.type.lower()
		if 'other' in filament_type:
			self.warningStaticText.SetLabel(_("This setting must be used with caution!"))
			self.warningStaticText.SetForegroundColour((169, 68, 66))
			self.temperatureSpinCtrl.Enable(True)
		else:
			calculated_print_temperature += self.temp_preci
			self.warningStaticText.SetLabel(_("Filament approved by Dagoma."))
			self.warningStaticText.SetForegroundColour((60, 118, 61))
			self.temperatureSpinCtrl.Enable(False)
		profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
		self.temperatureSpinCtrl.SetValue(calculated_print_temperature)
		profile.putProfileSetting('filament_diameter', fila.filament_diameter)
		profile.putProfileSetting('filament_flow', fila.filament_flow)
		profile.putProfileSetting('retraction_speed', fila.retraction_speed)
		profile.putProfileSetting('retraction_amount', fila.retraction_amount)
		profile.putProfileSetting('filament_physical_density', fila.filament_physical_density)
		profile.putProfileSetting('filament_cost_kg', fila.filament_cost_kg)
		profile.putPreference('model_colour', fila.model_colour)
		if 'wood' in filament_type or 'flex' in filament_type:
			self.precisionRadioBox.Enable(False)
		else:
			self.precisionRadioBox.Enable(True)
			precision_index = int(profile.getPreference('precision_index'))
			fila = self.precisions[precision_index]
		profile.putProfileSetting('layer_height', fila.layer_height)
		profile.putProfileSetting('solid_layer_thickness', fila.solid_layer_thickness)
		profile.putProfileSetting('wall_thickness', fila.wall_thickness)
		profile.putProfileSetting('print_speed', fila.print_speed)
		profile.putProfileSetting('travel_speed', fila.travel_speed)
		profile.putProfileSetting('bottom_layer_speed', fila.bottom_layer_speed)
		profile.putProfileSetting('infill_speed', fila.infill_speed)
		profile.putProfileSetting('inset0_speed', fila.inset0_speed)
		profile.putProfileSetting('insetx_speed', fila.insetx_speed)

		self.colorComboBox.Clear()
		filaments = self.configuration.getElementsByTagName("Filament")
		colors = filaments[filament_index].getElementsByTagName("Color")
		self.colors = []
		if len(colors) > 0:
			self.colorComboBox.Enable(True)
			for color in colors:
				if color.hasAttributes():
					current_color = self.Color()
					current_color.label = color.getAttribute("name")
					current_color.name = _(current_color.label)
					self.colors.append(current_color)
		else:
			self.colorComboBox.Enable(False)
		self.colors.sort(key=lambda color: color.name)
		generic_color = self.Color()
		generic_color.label = 'Generic'
		generic_color.name = _(generic_color.label)
		self.colors.insert(0, generic_color)
		for color in self.colors:
			self.colorComboBox.Append(color.name)

		if not self.alreadyLoaded:
			color_label = profile.getPreference('color_label')
			self.colorComboBox.SetStringSelection(_(color_label))
			self.alreadyLoaded = True
		else:
			self.colorComboBox.SetSelection(0)
			profile.putPreference('color_label', 'Generic')

	def RefreshColor(self):
		#print 'Refresh color'
		color_index = self.colorComboBox.GetSelection()
		color_label = self.colors[color_index].label
		profile.putPreference('color_label', color_label)
		filament_index = int(profile.getPreference('filament_index'))
		fila = self.filaments[filament_index]
		if color_index > 0:
			filaments = self.configuration.getElementsByTagName("Filament")
			colors = filaments[filament_index].getElementsByTagName("Color")
			colors.sort(key=lambda color: _(color.getAttribute("name")))
			color = colors[color_index - 1]

			print_temperature_tags = color.getElementsByTagName("print_temperature")
			if len(print_temperature_tags) > 0:
				print_temperature = float(print_temperature_tags[0].firstChild.nodeValue)
			else:
				print_temperature = float(fila.print_temperature)
			if not self.temperatureSpinCtrl.IsEnabled():
				print_temperature += self.temp_preci
			self.temperatureSpinCtrl.SetValue(print_temperature)
			profile.putProfileSetting('print_temperature', str(print_temperature))

			grip_temperature_tags = color.getElementsByTagName("grip_temperature")
			if len(grip_temperature_tags) > 0:
				grip_temperature = print_temperature_tags[0].firstChild.nodeValue
			else:
				grip_temperature = fila.grip_temperature
			profile.putProfileSetting('grip_temperature', str(grip_temperature))

			filament_diameter_tags = color.getElementsByTagName("filament_diameter")
			if len(filament_diameter_tags) > 0:
				filament_diameter = filament_diameter_tags[0].firstChild.nodeValue
			else:
				filament_diameter = fila.filament_diameter
			profile.putProfileSetting('filament_diameter', str(filament_diameter))

			filament_flow_tags = color.getElementsByTagName("filament_flow")
			if len(filament_flow_tags) > 0:
				filament_flow = filament_flow_tags[0].firstChild.nodeValue
			else:
				filament_flow = fila.filament_flow
			profile.putProfileSetting('filament_flow', str(filament_flow))

			retraction_speed_tags = color.getElementsByTagName("retraction_speed")
			if len(retraction_speed_tags) > 0:
				retraction_speed = retraction_speed_tags[0].firstChild.nodeValue
			else:
				retraction_speed = fila.retraction_speed
			profile.putProfileSetting('retraction_speed', str(retraction_speed))

			retraction_amount_tags = color.getElementsByTagName("retraction_amount")
			if len(retraction_amount_tags) > 0:
				retraction_amount = retraction_amount_tags[0].firstChild.nodeValue
			else:
				retraction_amount = fila.retraction_amount
			profile.putProfileSetting('retraction_amount', str(retraction_amount))

			filament_physical_density_tags = color.getElementsByTagName("filament_physical_density")
			if len(filament_physical_density_tags) > 0:
				filament_physical_density = filament_physical_density_tags[0].firstChild.nodeValue
			else:
				filament_physical_density = fila.filament_physical_density
			profile.putProfileSetting('filament_physical_density', str(filament_physical_density))

			filament_cost_kg_tags = color.getElementsByTagName("filament_cost_kg")
			if len(filament_cost_kg_tags) > 0:
				filament_cost_kg = filament_cost_kg_tags[0].firstChild.nodeValue
			else:
				filament_cost_kg = fila.filament_cost_kg
			profile.putProfileSetting('filament_cost_kg', str(filament_cost_kg))

			model_colour_tags = color.getElementsByTagName("model_colour")
			if len(model_colour_tags) > 0:
				model_colour = model_colour_tags[0].firstChild.nodeValue
			else:
				model_colour = fila.model_colour
			profile.putPreference('model_colour', model_colour)
		else:
			print_temperature = float(fila.print_temperature)
			if not self.temperatureSpinCtrl.IsEnabled():
				print_temperature += self.temp_preci
			self.temperatureSpinCtrl.SetValue(print_temperature)
			profile.putProfileSetting('print_temperature', str(print_temperature))
			profile.putProfileSetting('grip_temperature', fila.grip_temperature)
			profile.putProfileSetting('filament_diameter', fila.filament_diameter)
			profile.putProfileSetting('filament_flow', fila.filament_flow)
			profile.putProfileSetting('retraction_speed', fila.retraction_speed)
			profile.putProfileSetting('retraction_amount', fila.retraction_amount)
			profile.putProfileSetting('filament_physical_density', fila.filament_physical_density)
			profile.putProfileSetting('filament_cost_kg', fila.filament_cost_kg)
			profile.putPreference('model_colour', fila.model_colour)

	def RefreshTemperatureSpinCtrl(self):
		#print 'Refresh Spin'
		profile.putProfileSetting('print_temperature', str(self.temperatureSpinCtrl.GetValue()))

	def RefreshFilling(self):
		fill_index = self.fillingRadioBox.GetSelection()
		filling = self.fillings[fill_index]
		profile.putPreference('fill_index', fill_index)
		profile.putProfileSetting('fill_density', filling.fill_density)
		profile.putProfileSetting('spiralize', filling.spiralize)

	def RefreshPrecision(self):
		precision_index = self.precisionRadioBox.GetSelection()
		profile.putPreference('precision_index', precision_index)
		preci = self.precisions[precision_index]
		filament_index = int(profile.getPreference('filament_index'))
		filament = self.filaments[filament_index]
		filament_type = filament.type.lower()
		if 'wood' in filament_type or 'flex' in filament_type:
			preci = filament
		profile.putProfileSetting('layer_height', preci.layer_height)
		profile.putProfileSetting('solid_layer_thickness', preci.solid_layer_thickness)
		profile.putProfileSetting('wall_thickness', preci.wall_thickness)
		profile.putProfileSetting('print_speed', preci.print_speed)
		new_temp_preci = float(preci.temp_preci)
		calculated_print_temperature = float(profile.getProfileSetting('print_temperature'))
		if not self.temperatureSpinCtrl.IsEnabled():
			calculated_print_temperature += new_temp_preci
			try:
				calculated_print_temperature -= self.temp_preci
			except:
				pass
		self.temp_preci = new_temp_preci
		self.temperatureSpinCtrl.SetValue(calculated_print_temperature)
		profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
		profile.putProfileSetting('travel_speed', preci.travel_speed)
		profile.putProfileSetting('bottom_layer_speed', preci.bottom_layer_speed)
		# Speed
		profile.putProfileSetting('infill_speed', preci.infill_speed)
		profile.putProfileSetting('inset0_speed', preci.inset0_speed)
		profile.putProfileSetting('insetx_speed', preci.insetx_speed)

		# Refresh layer heights according to quality...
		for panel in self.pausePluginPanel.panelList:
			panelChildren = panel.GetSizer().GetChildren()
			height_value = None
			layerWidget = None
			heightWidget = None
			for panelChild in panelChildren:
				panelWidget = panelChild.GetWindow()
				# The only enabled textctrl by line is the one containing the layer info
				if isinstance(panelWidget, wx.TextCtrl) and panelWidget.IsEnabled():
					layerWidget = panelWidget
				# The only disabled textctrl by line is the one containing the height info
				if isinstance(panelWidget, wx.TextCtrl) and not panelWidget.IsEnabled():
					heightWidget = panelWidget
			heightValue = heightWidget.GetValue().split(' mm')[0]
			layerWidget.SetValue(str(int(float(heightValue) / float(preci.layer_height))))

	def RefreshPrinterHead(self):
		printerhead_index = self.printerHeadRadioBox.GetSelection()
		printerhead = self.heads[printerhead_index]
		profile.putPreference('printerhead_index', printerhead_index)
		profile.putProfileSetting('fan_speed', printerhead.fan_speed)
		profile.putProfileSetting('cool_min_layer_time', printerhead.cool_min_layer_time)

	def RefreshSupport(self):
		supp = self.supports[self.supportRadioBox.GetSelection()]
		profile.putProfileSetting('support', supp.support)

	def RefreshAdhesion(self):
		if self.adhesionCheckBox.GetValue():
			profile.putProfileSetting('platform_adhesion', self.adhesions[0].platform_adhesion)
		else:
			profile.putProfileSetting('platform_adhesion', self.adhesions[1].platform_adhesion)

	def IsNumber(self, zeString):
		try:
			float(zeString)
			return True
		except ValueError:
			return False

	def CalculateZOffset(self):
		printing_surface_height = float(profile.getProfileSetting('printing_surface_height'))
		offset_input = float(profile.getProfileSetting('offset_input'))
		offset_value = offset_input - printing_surface_height
		profile.putProfileSetting('offset_value', offset_value)

	def RefreshPrintingSurface(self):
		prtsurf = self.printing_surfaces[self.printingSurfaceRadioBox.GetSelection()]
		profile.putProfileSetting('printing_surface_name', prtsurf.name)
		profile.putProfileSetting('printing_surface_height', prtsurf.height)
		self.CalculateZOffset()

	def RefreshOffset(self):
		value = self.offsetTextCtrl.GetValue()
		if self.IsNumber(value) :
			profile.putProfileSetting('offset_input', value)
			self.CalculateZOffset()
		else :
			self.offsetTextCtrl.SetValue(profile.getProfileSetting('offset_input'))

	def RefreshSensor(self):
		if self.sensorCheckBox.GetValue():
			sensor = self.sensors[0].sensor
		else:
			sensor = self.sensors[1].sensor
		profile.putProfileSetting('sensor', sensor)

	def OnSupportRadioBoxChanged(self, event):
		self.RefreshSupport()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnAdhesionCheckBoxChanged(self, event):
		self.RefreshAdhesion()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnPrecisionRadioBoxChanged(self, event):
		self.RefreshPrecision()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnPrinterHeadRadioBoxChanged(self, event):
		self.RefreshPrinterHead()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnFillingRadioBoxChanged(self, event):
		self.RefreshFilling()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnFilamentComboBoxChanged(self, event):
		self.RefreshFilament()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnColorComboBoxChanged(self, event):
		self.RefreshColor()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnTemperatureSpinCtrlChanged(self, event):
		self.RefreshTemperatureSpinCtrl()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnPrintingSurfaceRadioBoxChanged(self, event):
		self.RefreshPrintingSurface()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnOffsetTextCtrlChanged(self, event):
		self.RefreshOffset()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnSensorCheckBoxChanged(self, event):
		self.RefreshSensor()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnPreparePrintButtonClick(self, event):
		profile.printSlicingInfo()
		self.GetParent().GetParent().GetParent().scene.OnPrintButton(1)
		event.Skip()

	def OnPauseButtonClick(self, event):
		scene_viewSelection = self.GetParent().GetParent().GetParent().scene.viewSelection
		if scene_viewSelection.getValue() == 0:
			scene_viewSelection.setValue(1)
		else:
			scene_viewSelection.setValue(0)
		event.Skip()

	def OnSize(self, e):
		e.Skip()

	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		self.pausePluginPanel.updateProfileToControls()
