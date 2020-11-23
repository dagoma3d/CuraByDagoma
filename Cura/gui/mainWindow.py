#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import platform
import wx
import os
import webbrowser
import sys
import wx.lib.agw.hyperlink as hl
from wx.lib import scrolledpanel

from Cura.gui import configBase
from Cura.gui import pausePluginPanel
from Cura.gui import configWizard
from Cura.gui import sceneView
from Cura.gui import aboutWindow
from Cura.gui import warningWindow
from Cura.gui.util import dropTarget
from Cura.gui.tools import pidDebugger
from Cura.util import profile
from Cura.util import version
from Cura.util import myversion
from Cura.util import meshLoader
from Cura.util import resources
from xml.dom import minidom

class mainWindow(wx.Frame):
	def __init__(self):
		self.windowTitle = 'Cura by Dagoma ' + os.environ['CURABYDAGO_VERSION']
		super(mainWindow, self).__init__(None, title=self.windowTitle, pos=(0, 0), size=wx.DisplaySize())

		self.Bind(wx.EVT_CLOSE, self.OnClose)

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
				view.registerForDraggedTypes_(['NSFilenamesPboardType'])
			except:
				pass

		self.isLatest = myversion.isLatest()

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(localFilename=mruFile, style=wx.CONFIG_USE_LOCAL_FILE)

		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in range(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in range(10)]
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
			i = self.languagesMenu.Append(-1, _(language[1]), _('You have to restart the application to load the correct language.'), wx.ITEM_RADIO)
			if profile.getPreference('language') == language[1]:
				i.Check(True)
			else:
				i.Check(False)
			def OnLanguageSelect(e, selected_language=language[1]):
				profile.putPreference('language', selected_language)
				warningBox = warningWindow.warningWindow(self, _('You have to restart the application to load the correct language.'))
				warningBox.Centre()
				warningBox.Show()
				if sys.platform.startswith('darwin'):
					from Cura.gui.util import macosFramesWorkaround as mfw
					wx.CallAfter(mfw.StupidMacOSWorkaround)
			self.Bind(wx.EVT_MENU, OnLanguageSelect, i)
		self.settingsMenu.AppendSubMenu(self.languagesMenu, _("Language"))
		i = self.settingsMenu.Append(wx.ID_ANY, _("Printer"), _("Choose the printer you want to use."))
		self.Bind(wx.EVT_MENU, self.OnPrinterWindow, i)
		self.menuBar.Append(self.settingsMenu, _("Preferences"))

		contactUrl = _("contact_url")
		buyUrl = _("buy_url")
		helpUrl = _("help_url")
		self.helpMenu = wx.Menu()
		i = self.helpMenu.Append(wx.ID_ANY, _("Contact us"), _("Contact us for any further information."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(contactUrl), i)
		i = self.helpMenu.Append(wx.ID_ANY, _("Buy filament"), _("Buy filament on our website."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(buyUrl), i)
		i = self.helpMenu.Append(wx.ID_HELP, _("Online help"), _("Online help to fine tune your settings."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(helpUrl), i)
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
		self.normalSettingsPanel = normalSettingsPanel(self.optionsPane, self.isLatest, lambda : self.scene.sceneUpdated())

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
		if wx.Display.GetFromPoint((self.GetPosition().x + self.GetSize().x, self.GetPosition().y + self.GetSize().y)) < 0:
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
		try:
			path = self.modelFileHistory.GetHistoryFile(0)
			profile.putPreference('lastFile', path)
		except:
			pass

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
		self.normalSettingsPanel = normalSettingsPanel(self.optionsPane, self.isLatest, lambda : self.scene.sceneUpdated())
		self.optionsSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.optionsPane.SetSizerAndFit(self.optionsSizer)
		self.UpdateProfileToAllControls()

	def OnPrinterWindow(self, e):
		configWizard.ConfigWizard(self, False)
		#printerBox = configWizard.ConfigWizard(self)
		#printerBox.Centre()
		#printerBox.Show()
		if sys.platform.startswith('darwin'):
			from Cura.gui.util import macosFramesWorkaround as mfw
			wx.CallAfter(mfw.StupidMacOSWorkaround)

	def OnAbout(self, e):
		aboutBox = aboutWindow.aboutWindow(self)
		aboutBox.Centre()
		aboutBox.Show()
		if sys.platform.startswith('darwin'):
			from Cura.gui.util import macosFramesWorkaround as mfw
			wx.CallAfter(mfw.StupidMacOSWorkaround)

	def OnClose(self, e):
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		profile.putPreference('window_normal_sash', int('-' + str(self.optionsPane.GetSize()[0])))

		#HACK: Set the paint function of the glCanvas to nothing so it won't keep refreshing. Which can keep wxWidgets from quiting.
		print("Closing down")
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
			self.solidarea_speed = None
			self.support_xy_distance = None
			self.support_z_distance = None

	class Color:
		def __init__(self):
			self.label = ''
			self.name = ''
	
	class Extruder:
		def __init__(self):
			self.name = 'Extruder 1'
			self.value = 0

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
			self.solidarea_speed = ''

	class Support:
		def __init__(self):
			self.name = 'None'
			self.support = 'None'

	class SupportDualExtrusion:
		def __init__(self):
			self.name = 'Both'
			self.support_dual_extrusion = 'Both'

	class WipeTowerVolume:
		def __init__(self):
			self.name = 'Normal'
			self.wipe_tower_volume = '65'

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

	def __init__(self, parent, isLatest, callback = None):
		super(normalSettingsPanel, self).__init__(parent, callback)
		self.isLatest = isLatest
		self.alreadyLoaded = False
		self.alreadyLoaded2 = False
		self.parent = parent
		self.loadConfiguration()
		self.warningStaticText = wx.StaticText(self, wx.ID_ANY)
		warningStaticTextFont = self.warningStaticText.GetFont()
		warningStaticTextFont.SetPointSize(10)
		warningStaticTextFont.SetWeight(wx.FONTWEIGHT_BOLD)
		self.warningStaticText.SetFont(warningStaticTextFont)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			self.warning2StaticText = wx.StaticText(self, wx.ID_ANY)
			warning2StaticTextFont = self.warning2StaticText.GetFont()
			warning2StaticTextFont.SetPointSize(10)
			warning2StaticTextFont.SetWeight(wx.FONTWEIGHT_BOLD)
			self.warning2StaticText.SetFont(warning2StaticTextFont)
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.colorComboBox = wx.Choice(self, wx.ID_ANY, choices = [])
			if int(profile.getMachineSetting('extruder_amount')) == 2:
				self.color2ComboBox = wx.Choice(self, wx.ID_ANY, choices = [])
		else:
			self.colorComboBox = wx.ComboBox(self, wx.ID_ANY, choices = [] , style=wx.CB_DROPDOWN | wx.CB_READONLY)
			if int(profile.getMachineSetting('extruder_amount')) == 2:
				self.color2ComboBox = wx.ComboBox(self, wx.ID_ANY, choices = [] , style=wx.CB_DROPDOWN | wx.CB_READONLY)

		self.temperatureText = wx.StaticText(self, wx.ID_ANY, _(("Temperature (°C) :")))
		self.temperatureSpinCtrl = wx.SpinCtrl(self, wx.ID_ANY, profile.getProfileSetting('print_temperature'), min=175, max=255, style=wx.SP_ARROW_KEYS | wx.TE_AUTO_URL)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			self.temperature2Text = wx.StaticText(self, wx.ID_ANY, _(("Temperature (°C) :")))
			self.temperature2SpinCtrl = wx.SpinCtrl(self, wx.ID_ANY, profile.getProfileSetting('print_temperature2'), min=175, max=255, style=wx.SP_ARROW_KEYS | wx.TE_AUTO_URL)
		self.printButton = wx.Button(self, wx.ID_ANY, _("Prepare the Print"))

		self.offsetStaticText = wx.StaticText(self, wx.ID_ANY, _("Offset (mm) :"))
		self.offsetTextCtrl = wx.TextCtrl(self, -1, profile.getProfileSetting('offset_input'))

		# Pause plugin
		self.pausePluginButton = wx.Button(self, wx.ID_ANY, _(("Color change(s)")))
		pausePluginButtonToolTip = wx.ToolTip(_("If you don't have any pause button on your printer...\nJust push the X endstop to resume your print!"))
		self.pausePluginButton.SetToolTip(pausePluginButtonToolTip)
		self.pausePluginPanel = pausePluginPanel.pausePluginPanel(self, callback)
		self.__setProperties()
		self.__doLayout()

		self.RefreshSupport()
		self.RefreshPrecision()
		self.RefreshFilament()
		self.RefreshColor()
		self.RefreshTemperatureSpinCtrl()
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			self.RefreshFilament2()
			self.RefreshColor2()
			self.RefreshTemperature2SpinCtrl()
			self.RefreshStartExtruder()
			self.RefreshSupportDualExtrusion()
			self.RefreshWipeTowerVolume()
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
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			if sys.platform == 'darwin':
				self.Bind(wx.EVT_CHOICE, self.OnFilament2ComboBoxChanged, self.filament2ComboBox)
				self.Bind(wx.EVT_CHOICE, self.OnColor2ComboBoxChanged, self.color2ComboBox)
			else:
				self.Bind(wx.EVT_COMBOBOX, self.OnFilament2ComboBoxChanged, self.filament2ComboBox)
				self.Bind(wx.EVT_COMBOBOX, self.OnColor2ComboBoxChanged, self.color2ComboBox)
			self.Bind(wx.EVT_TEXT, self.OnTemperature2SpinCtrlChanged, self.temperature2SpinCtrl)
			self.Bind(wx.EVT_TEXT_ENTER, self.OnTemperature2SpinCtrlChanged, self.temperature2SpinCtrl)
			self.Bind(wx.EVT_SPINCTRL, self.OnTemperature2SpinCtrlChanged, self.temperature2SpinCtrl)
		self.Bind(wx.EVT_RADIOBOX, self.OnPrecisionRadioBoxChanged, self.precisionRadioBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnSupportRadioBoxChanged, self.supportRadioBox)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			self.Bind(wx.EVT_RADIOBOX, self.OnStartExtruderRadioBoxChanged, self.startExtruderRadioBox)
			self.Bind(wx.EVT_RADIOBOX, self.OnSupportDualExtrusionRadioBoxChanged, self.supportExtruderDualExtrusionRadioBox)
			self.Bind(wx.EVT_RADIOBOX, self.OnWipeTowerVolumeRadioBoxChanged, self.wipeTowerVolumeRadioBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnFillingRadioBoxChanged, self.fillingRadioBox)
		self.Bind(wx.EVT_CHECKBOX, self.OnSensorCheckBoxChanged,self.sensorCheckBox)
		self.Bind(wx.EVT_RADIOBOX, self.OnPrintingSurfaceRadioBoxChanged, self.printingSurfaceRadioBox)
		self.Bind(wx.EVT_TEXT, self.OnOffsetTextCtrlChanged, self.offsetTextCtrl)
		self.Bind(wx.EVT_CHECKBOX, self.OnAdhesionCheckBoxChanged, self.adhesionCheckBox)
		self.Bind(wx.EVT_BUTTON, self.OnPreparePrintButtonClick, self.printButton)
		self.Bind(wx.EVT_BUTTON, self.OnPauseButtonClick, self.pausePluginButton)

	def __setProperties(self):
		self.temperatureSpinCtrl.Enable(False)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			self.temperature2SpinCtrl.Enable(False)
			self.startExtruderRadioBox.SetSelection(0)
		self.supportRadioBox.SetSelection(0)


	def __doLayout(self):
		printerName = profile.getMachineSetting('machine_name')
		self.pausePluginButton.Disable()
		self.printButton.Disable()

		buyUrl = _("buy_url") + "&utm_campaign=achat_filament_" + profile.getMachineSetting('machine_name').lower()
		helpUrl = _("help_url") + "&utm_campaign=aide_" + profile.getMachineSetting('machine_name').lower()
		filamentSizer = wx.BoxSizer(wx.HORIZONTAL)
		filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, _("Filament")))
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, " 1 ("))
		else:
			filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, " ("))
		filamentSizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Buy filament"), URL=buyUrl))
		filamentSizer.Add(wx.StaticText(self, wx.ID_ANY, "):"))

		if int(profile.getMachineSetting('extruder_amount')) == 2:
			filament2Sizer = wx.BoxSizer(wx.HORIZONTAL)
			filament2Sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Filament")))
			filament2Sizer.Add(wx.StaticText(self, wx.ID_ANY, " 2 ("))
			filament2Sizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Buy filament"), URL=buyUrl))
			filament2Sizer.Add(wx.StaticText(self, wx.ID_ANY, "):"))

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		if not self.isLatest:
			mainSizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("New version available!"), URL="https://dist.dagoma3d.com/CuraByDagoma"), flag=wx.EXPAND|wx.BOTTOM, border=2)
		else:
			mainSizer.Add(wx.StaticText(self, wx.ID_ANY, _("Up to date software")), flag=wx.EXPAND|wx.BOTTOM, border=2)
		mainSizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(filamentSizer)
		mainSizer.Add(self.filamentComboBox, flag=wx.EXPAND|wx.BOTTOM, border=2)
		mainSizer.Add(self.colorComboBox, flag=wx.EXPAND)
		mainSizer.Add(self.warningStaticText)
		mainSizer.Add(self.temperatureText)
		mainSizer.Add(self.temperatureSpinCtrl, flag=wx.EXPAND|wx.BOTTOM, border=2)
		mainSizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.BOTTOM, border=5)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			mainSizer.Add(filament2Sizer)
			mainSizer.Add(self.filament2ComboBox, flag=wx.EXPAND|wx.BOTTOM, border=2)
			mainSizer.Add(self.color2ComboBox, flag=wx.EXPAND)
			mainSizer.Add(self.warning2StaticText)
			mainSizer.Add(self.temperature2Text)
			mainSizer.Add(self.temperature2SpinCtrl, flag=wx.EXPAND|wx.BOTTOM, border=2)
			mainSizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, _("Fine tune your settings"), URL=helpUrl), flag=wx.EXPAND|wx.BOTTOM, border=2)
		mainSizer.Add(wx.StaticLine(self, -1), flag=wx.EXPAND|wx.BOTTOM, border=5)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			mainSizer.Add(self.startExtruderRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(self.fillingRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(self.precisionRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		mainSizer.Add(self.supportRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			mainSizer.Add(self.supportExtruderDualExtrusionRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		if printerName == "DiscoVery200":
			mainSizer.Add(self.printingSurfaceRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
			mainSizer.Add(self.offsetStaticText, flag=wx.EXPAND)
			mainSizer.Add(self.offsetTextCtrl, flag=wx.EXPAND|wx.BOTTOM, border=5)
		else:
			self.printingSurfaceRadioBox.Hide()
			self.offsetStaticText.Hide()
			self.offsetTextCtrl.Hide()
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			mainSizer.Add(self.wipeTowerVolumeRadioBox, flag=wx.EXPAND|wx.BOTTOM, border=5)
		if not printerName in ["Neva", "Magis"]:
			mainSizer.Add(self.sensorCheckBox)
		else:
			self.sensorCheckBox.Hide()
		mainSizer.Add(self.adhesionCheckBox, flag=wx.BOTTOM, border=5)
		mainSizer.Add(self.pausePluginButton, flag=wx.EXPAND)
		mainSizer.Add(self.pausePluginPanel, flag=wx.EXPAND)
		mainSizer.Add(self.printButton, flag=wx.EXPAND|wx.TOP, border=5)

		self.SetSizerAndFit(mainSizer)
		self.Layout()

	def setParameterToObject(self, paramName, destObject, parentTag, alternativeParentTag = None):
		param_tags = parenTag.getElementsByTagName(paramName)
		if len(param_tags) > 0:
			setattr(destObject, paramName, param_tags[0].firstChild.nodeValue)
		elif alternativeParentTag is not None:
			param_tags = alternativeParentTag.getElementsByTagName(paramName)
			setattr(destObject, paramName, param_tags[0].firstChild.nodeValue)

	def loadConfiguration(self):
		xmlFile = profile.getPreference('xml_file')
		self.configuration = minidom.parse(resources.getPathForXML(xmlFile))
		self.initPrinter()
		self.initConfiguration()
		self.initGCode()
		self.initFilament()
		self.initFilling()
		self.initPrecision()
		self.initSupport()
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			self.initExtruder()
			self.initSupportDualExtrusion()
			self.initWipeTowerVolume()
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
					if paramName == 'oneAtATime':
						profile.putPreference('oneAtATime', paramValue)
					if paramName != 'machine_width' or (paramName == 'machine_width' and profile.getMachineSetting('machine_name') not in ['DiscoEasy200', 'DiscoUltimate']):
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

		if int(profile.getMachineSetting('extruder_amount')) == 2:
			gcode_preswitch = gcode.getElementsByTagName("GpreswitchT0")[0].firstChild.nodeValue
			profile.putAlterationSetting('preSwitchExtruder.gcode', gcode_preswitch)

			gcode_postswitch = gcode.getElementsByTagName("GpostswitchT0")[0].firstChild.nodeValue
			profile.putAlterationSetting('postSwitchExtruder.gcode', gcode_postswitch)

			gcode_preswitch = gcode.getElementsByTagName("GpreswitchT1")[0].firstChild.nodeValue
			profile.putAlterationSetting('preSwitchExtruder2.gcode', gcode_preswitch)

			gcode_postswitch = gcode.getElementsByTagName("GpostswitchT1")[0].firstChild.nodeValue
			profile.putAlterationSetting('postSwitchExtruder2.gcode', gcode_postswitch)
		else:
			profile.putAlterationSetting('preSwitchExtruder.gcode', '')
			profile.putAlterationSetting('postSwitchExtruder.gcode', '')
			profile.putAlterationSetting('preSwitchExtruder2.gcode', '')
			profile.putAlterationSetting('postSwitchExtruder2.gcode', '')

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
				support_xy_distance_tags = filament.getElementsByTagName("support_xy_distance")
				if len(support_xy_distance_tags) > 0:
					fila.support_xy_distance = support_xy_distance_tags[0].firstChild.nodeValue
				else:
					support_xy_distance_tags = self.configuration.getElementsByTagName('Configuration')[0].getElementsByTagName("support_xy_distance")
					fila.support_xy_distance = support_xy_distance_tags[0].firstChild.nodeValue
				support_z_distance_tags = filament.getElementsByTagName("support_z_distance")
				if len(support_z_distance_tags) > 0:
					fila.support_z_distance = support_z_distance_tags[0].firstChild.nodeValue
				else:
					support_z_distance_tags = self.configuration.getElementsByTagName('Configuration')[0].getElementsByTagName("support_z_distance")
					fila.support_z_distance = support_z_distance_tags[0].firstChild.nodeValue
				layer_height_tags = filament.getElementsByTagName("layer_height")
				if len(layer_height_tags) > 0:
					fila.layer_height = layer_height_tags[0].firstChild.nodeValue
				solid_layer_thickness_tags = filament.getElementsByTagName("solid_layer_thickness")
				if len(solid_layer_thickness_tags) > 0:
					fila.solid_layer_thickness = solid_layer_thickness_tags[0].firstChild.nodeValue
				wall_thickness_tags = filament.getElementsByTagName("wall_thickness")
				if len(wall_thickness_tags) > 0:
					fila.wall_thickness = wall_thickness_tags[0].firstChild.nodeValue
				print_speed_tags = filament.getElementsByTagName("print_speed")
				if len(print_speed_tags) > 0:
					fila.print_speed = print_speed_tags[0].firstChild.nodeValue
				travel_speed_tags = filament.getElementsByTagName("travel_speed")
				if len(travel_speed_tags) > 0:
					fila.travel_speed = travel_speed_tags[0].firstChild.nodeValue
				bottom_layer_speed_tags = filament.getElementsByTagName("bottom_layer_speed")
				if len(bottom_layer_speed_tags) > 0:
					fila.bottom_layer_speed = bottom_layer_speed_tags[0].firstChild.nodeValue
				infill_speed_tags = filament.getElementsByTagName("infill_speed")
				if len(infill_speed_tags) > 0:
					fila.infill_speed = infill_speed_tags[0].firstChild.nodeValue
				inset0_speed_tags = filament.getElementsByTagName("inset0_speed")
				if len(inset0_speed_tags) > 0:
					fila.inset0_speed = inset0_speed_tags[0].firstChild.nodeValue
				insetx_speed_tags = filament.getElementsByTagName("insetx_speed")
				if len(insetx_speed_tags) > 0:
					fila.insetx_speed = insetx_speed_tags[0].firstChild.nodeValue
				solidarea_speed_tags = filament.getElementsByTagName("solidarea_speed")
				if len(solidarea_speed_tags) > 0:
					fila.solidarea_speed = solidarea_speed_tags[0].firstChild.nodeValue
				self.filaments.append(fila)
			except:
				print('Some Error in Filament Bloc')
				pass

		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.filamentComboBox = wx.Choice(self, wx.ID_ANY, choices = choices)
		else:
			self.filamentComboBox = wx.ComboBox(self, wx.ID_ANY, choices = choices , style=wx.CB_DROPDOWN | wx.CB_READONLY)

		filament_selection_index = profile.getPreferenceInt('filament_index')
		if filament_selection_index >= len(filaments):
			filament_selection_index = 0
			profile.putPreference('filament_index', 0)
		self.filamentComboBox.SetSelection(filament_selection_index)

		if int(profile.getMachineSetting('extruder_amount')) == 2:
			if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
				self.filament2ComboBox = wx.Choice(self, wx.ID_ANY, choices = choices)
			else:
				self.filament2ComboBox = wx.ComboBox(self, wx.ID_ANY, choices = choices , style=wx.CB_DROPDOWN | wx.CB_READONLY)

			filament2_selection_index = profile.getPreferenceInt('filament2_index')
			if filament2_selection_index >= len(filaments):
				filament2_selection_index = 0
				profile.putPreference('filament2_index', 0)
			self.filament2ComboBox.SetSelection(filament2_selection_index)

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
					print('Some Errors in Filling Bloc')
					pass
		self.fillingRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Filling density :"), choices = choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

		fill_selection_index = profile.getPreferenceInt('fill_index')
		if fill_selection_index >= len(fillings):
			if len(fillings) >= 3:
				fill_selection_index = 2
			else:
				fill_selection_index = 0
			profile.putPreference('fill_index', fill_selection_index)

		if int(profile.getMachineSetting('extruder_amount')) == 2:
			if fill_selection_index == 0:
				if len(fillings) >= 3:
					fill_selection_index = 2
				else:
					fill_selection_index = 1
				profile.putPreference('fill_index', 1)
			self.fillingRadioBox.EnableItem(0, False)
		self.fillingRadioBox.SetSelection(fill_selection_index)
	
	def initExtruder(self):
		extruders = [
			{'name': 'Extruder', 'value': 0},
			{'name': 'Extruder', 'value': 1},
		]
		choices = []
		self.extruders = []
		for extruder in extruders:
			extru = self.Extruder()
			name = _(extruder.get("name") + " %d") % (extruder.get("value") + 1)
			choices.append(name)
			extru.name = name
			try :
				extru.value = extruder.get("value")
				self.extruders.append(extru)
			except :
				print('Some Error in Extruders Bloc')
				pass
		self.startExtruderRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Start print with :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

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
					preci.solidarea_speed = precision.getElementsByTagName("solidarea_speed")[0].firstChild.nodeValue
					self.precisions.append(preci)
				except :
					print('Some Error in Precision Bloc')
					pass
		self.precisionRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Quality (layer thickness) :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

		precision_selection_index = profile.getPreferenceInt('precision_index')
		if precision_selection_index >= len(precisions):
			precision_selection_index = 0
			profile.putPreference('precision_index', 0)
		self.precisionRadioBox.SetSelection(precision_selection_index)

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
			supp.name = name
			try :
				supp.support = support.get("value")
				self.supports.append(supp)
			except :
				print('Some Error in Supports Bloc')
				pass
		self.supportRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Printing supports :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

	def initSupportDualExtrusion(self):
		support_dual_extrusions = [
			{'name': 'Both', 'value': 'Both'},
			{'name': 'Filament 1', 'value': 'First extruder'},
			{'name': 'Filament 2', 'value': 'Second extruder'}
		]
		choices = []
		self.support_dual_extrusions = []
		for support_dual_extrusion in support_dual_extrusions:
			suppDualExtrusion = self.SupportDualExtrusion()
			name = support_dual_extrusion.get("name")
			choices.append(_(name))
			suppDualExtrusion.name = name
			try :
				suppDualExtrusion.support_dual_extrusion = support_dual_extrusion.get("value")
				self.support_dual_extrusions.append(suppDualExtrusion)
			except :
				print('Some Error in Support Bloc')
				pass

		self.supportExtruderDualExtrusionRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Filament(s) for support :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		support_dual_extrusion_index = profile.getPreferenceInt('support_dual_extrusion_index')
		self.supportExtruderDualExtrusionRadioBox.SetSelection(support_dual_extrusion_index)

	def initWipeTowerVolume(self):
		wipe_tower_volumes = self.configuration.getElementsByTagName("WipeTower")
		choices = []
		self.wipe_tower_volumes = []
		for wipe_tower_volume in wipe_tower_volumes:
			wipeTowerVolume = self.WipeTowerVolume()
			name = wipe_tower_volume.getAttribute("name")
			choices.append(_(name))
			wipeTowerVolume.name = name
			try :
				wipeTowerVolume.wipe_tower_volume = wipe_tower_volume.getElementsByTagName("wipe_tower_volume")[0].firstChild.nodeValue
				self.wipe_tower_volumes.append(wipeTowerVolume)
			except :
				print('Some Error in Wipe tower volume Bloc')
				pass

		self.wipeTowerVolumeRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Wipe volume :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		wipe_tower_volume_index = profile.getPreferenceInt('wipe_tower_volume_index')
		if wipe_tower_volume_index >= len(wipe_tower_volumes):
			wipe_tower_volume_index = 0
			profile.putPreference('wipe_tower_volume_index', 0)
		self.wipeTowerVolumeRadioBox.SetSelection(wipe_tower_volume_index)

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
					print('Some Error in Printing Surface Bloc')
					pass

		if len(choices) == 0:
			name = "Generic"
			choices.append(name)
			prtsurf = self.PrintingSurface()
			prtsurf.name = name
			prtsurf.height = 0.0
			self.printing_surfaces.append(prtsurf)

		self.printingSurfaceRadioBox = wx.RadioBox(self, wx.ID_ANY, _("Printing surface :"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		printing_surface_name_index = profile.getPreferenceInt('printing_surface_name_index')
		if printing_surface_name_index >= len(printing_surfaces):
			printing_surface_name_index = 0
			profile.putPreference('printing_surface_name_index', 0)
		self.printingSurfaceRadioBox.SetSelection(printing_surface_name_index)

	def filamentType(self, fimament_comboBox):
		i = fimament_comboBox.GetSelection()
		f = self.filaments[i]
		return f.type.lower()

	def isSpecial(self, filament):
		return 'wood' in filament or 'flex' in filament or 'marble' in filament

	def isSpecialFilament1(self):
		t = self.filamentType(self.filamentComboBox)
		return self.isSpecial(t)

	def isSpecialFilament2(self):
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			t = self.filamentType(self.filament2ComboBox)
			return self.isSpecial(t)
		return False

	def hasAnySpecialFilament(self):
		return self.isSpecialFilament1() or self.isSpecialFilament2()



	def RefreshFilament(self):
		#print "Refresh fila"
		filament_index = self.filamentComboBox.GetSelection()
		fila = self.filaments[filament_index]
		profile.putPreference('filament_index', filament_index)
		profile.putPreference('filament_name', fila.type)
		calculated_print_temperature = int(float(fila.print_temperature))
		filament_type = fila.type.lower()
		if self.hasAnySpecialFilament():
			self.precisionRadioBox.SetSelection(0)
			self.precisionRadioBox.Enable(False)
		else:
			self.precisionRadioBox.Enable(True)
		self.RefreshPrecision()
		if 'other' in filament_type:
			self.warningStaticText.SetLabel(_("This setting must be used with caution!"))
			self.warningStaticText.SetForegroundColour((169, 68, 66))
			self.temperatureSpinCtrl.Enable(True)
		else:
			calculated_print_temperature += self.temp_preci
			self.warningStaticText.SetLabel(_("Filament approved by Dagoma."))
			self.warningStaticText.SetForegroundColour((60, 118, 61))
			self.temperatureSpinCtrl.Enable(False)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			filament2_index = self.filament2ComboBox.GetSelection()
			filament2_type = self.filaments[filament2_index].type.lower()
			if 'support' in filament_type:
				if 'support' in filament2_type:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(0)
					profile.putPreference('support_dual_extrusion_index', 0)
					profile.putProfileSetting('support_dual_extrusion', 'Both')
				else:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(1)
					profile.putPreference('support_dual_extrusion_index', 1)
					profile.putProfileSetting('support_dual_extrusion', 'First extruder')
			else:
				if 'support' in filament2_type:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(2)
					profile.putPreference('support_dual_extrusion_index', 2)
					profile.putProfileSetting('support_dual_extrusion', 'Second extruder')
				else:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(0)
					profile.putPreference('support_dual_extrusion_index', 0)
					profile.putProfileSetting('support_dual_extrusion', 'Both')
		profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
		self.temperatureSpinCtrl.SetValue(calculated_print_temperature)
		profile.putProfileSetting('filament_diameter', fila.filament_diameter)
		profile.putProfileSetting('filament_flow', fila.filament_flow)
		profile.putProfileSetting('retraction_speed', fila.retraction_speed)
		profile.putProfileSetting('retraction_amount', fila.retraction_amount)
		profile.putProfileSetting('filament_physical_density', fila.filament_physical_density)
		profile.putProfileSetting('filament_cost_kg', fila.filament_cost_kg)
		profile.putPreference('model_colour', fila.model_colour)
		profile.putProfileSetting('support_xy_distance', fila.support_xy_distance)
		profile.putProfileSetting('support_z_distance', fila.support_z_distance)
		if fila.layer_height is not None:
			profile.putProfileSetting('layer_height', fila.layer_height)
		if fila.solid_layer_thickness is not None:
			profile.putProfileSetting('solid_layer_thickness', fila.solid_layer_thickness)
		if fila.wall_thickness is not None:
			profile.putProfileSetting('wall_thickness', fila.wall_thickness)
		if fila.print_speed is not None:
			profile.putProfileSetting('print_speed', fila.print_speed)
		if fila.travel_speed is not None:
			profile.putProfileSetting('travel_speed', fila.travel_speed)
		if fila.bottom_layer_speed is not None:
			profile.putProfileSetting('bottom_layer_speed', fila.bottom_layer_speed)
		if fila.infill_speed is not None:
			profile.putProfileSetting('infill_speed', fila.infill_speed)
		if fila.inset0_speed is not None:
			profile.putProfileSetting('inset0_speed', fila.inset0_speed)
		if fila.insetx_speed is not None:
			profile.putProfileSetting('insetx_speed', fila.insetx_speed)
		if fila.solidarea_speed is not None:
			profile.putProfileSetting('solidarea_speed', fila.solidarea_speed)

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

	def RefreshFilament2(self):
		#print "Refresh fila"
		filament_index = self.filament2ComboBox.GetSelection()
		fila = self.filaments[filament_index]
		profile.putPreference('filament2_index', filament_index)
		profile.putPreference('filament2_name', fila.type)
		calculated_print_temperature = int(float(fila.print_temperature))
		filament_type = fila.type.lower()
		if self.hasAnySpecialFilament():
			self.precisionRadioBox.SetSelection(0)
			self.precisionRadioBox.Enable(False)
		else:
			self.precisionRadioBox.Enable(True)
		self.RefreshPrecision()
		if 'other' in filament_type:
			self.warning2StaticText.SetLabel(_("This setting must be used with caution!"))
			self.warning2StaticText.SetForegroundColour((169, 68, 66))
			self.temperature2SpinCtrl.Enable(True)
		else:
			calculated_print_temperature += self.temp_preci
			self.warning2StaticText.SetLabel(_("Filament approved by Dagoma."))
			self.warning2StaticText.SetForegroundColour((60, 118, 61))
			self.temperature2SpinCtrl.Enable(False)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			filament1_index = self.filamentComboBox.GetSelection()
			filament1_type = self.filaments[filament1_index].type.lower()
			if 'support' in filament_type:
				if 'support' in filament1_type:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(0)
					profile.putPreference('support_dual_extrusion_index', 0)
					profile.putProfileSetting('support_dual_extrusion', 'Both')
				else:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(2)
					profile.putPreference('support_dual_extrusion_index', 2)
					profile.putProfileSetting('support_dual_extrusion', 'Second extruder')
			else:
				if 'support' in filament1_type:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(1)
					profile.putPreference('support_dual_extrusion_index', 1)
					profile.putProfileSetting('support_dual_extrusion', 'First extruder')
				else:
					self.supportExtruderDualExtrusionRadioBox.SetSelection(0)
					profile.putPreference('support_dual_extrusion_index', 0)
					profile.putProfileSetting('support_dual_extrusion', 'Both')
		profile.putProfileSetting('print_temperature2', str(calculated_print_temperature))
		self.temperature2SpinCtrl.SetValue(calculated_print_temperature)
		profile.putProfileSetting('filament_diameter2', fila.filament_diameter)
		profile.putProfileSetting('filament_flow2', fila.filament_flow)
		profile.putProfileSetting('retraction_speed2', fila.retraction_speed)
		profile.putProfileSetting('retraction_amount2', fila.retraction_amount)
		profile.putProfileSetting('filament_physical_density2', fila.filament_physical_density)
		profile.putProfileSetting('filament_cost_kg2', fila.filament_cost_kg)
		profile.putPreference('model_colour2', fila.model_colour)
		profile.putProfileSetting('support_xy_distance', fila.support_xy_distance)
		profile.putProfileSetting('support_z_distance', fila.support_z_distance)
		if fila.layer_height is not None:
			profile.putProfileSetting('layer_height', fila.layer_height)
		if fila.solid_layer_thickness is not None:
			profile.putProfileSetting('solid_layer_thickness', fila.solid_layer_thickness)
		if fila.wall_thickness is not None:
			profile.putProfileSetting('wall_thickness', fila.wall_thickness)
		if fila.print_speed is not None:
			profile.putProfileSetting('print_speed', fila.print_speed)
		if fila.travel_speed is not None:
			profile.putProfileSetting('travel_speed', fila.travel_speed)
		if fila.bottom_layer_speed is not None:
			profile.putProfileSetting('bottom_layer_speed', fila.bottom_layer_speed)
		if fila.infill_speed is not None:
			profile.putProfileSetting('infill_speed', fila.infill_speed)
		if fila.inset0_speed is not None:
			profile.putProfileSetting('inset0_speed', fila.inset0_speed)
		if fila.insetx_speed is not None:
			profile.putProfileSetting('insetx_speed', fila.insetx_speed)
		if fila.solidarea_speed is not None:
			profile.putProfileSetting('solidarea_speed', fila.solidarea_speed)

		self.color2ComboBox.Clear()
		filaments = self.configuration.getElementsByTagName("Filament")
		colors = filaments[filament_index].getElementsByTagName("Color")
		self.colors2 = []
		if len(colors) > 0:
			self.color2ComboBox.Enable(True)
			for color in colors:
				if color.hasAttributes():
					current_color = self.Color()
					current_color.label = color.getAttribute("name")
					current_color.name = _(current_color.label)
					self.colors2.append(current_color)
		else:
			self.color2ComboBox.Enable(False)
		self.colors2.sort(key=lambda color: color.name)
		generic_color = self.Color()
		generic_color.label = 'Generic'
		generic_color.name = _(generic_color.label)
		self.colors2.insert(0, generic_color)
		for color in self.colors2:
			self.color2ComboBox.Append(color.name)

		if not self.alreadyLoaded2:
			color_label = profile.getPreference('color2_label')
			self.color2ComboBox.SetStringSelection(_(color_label))
			self.alreadyLoaded2 = True
		else:
			self.color2ComboBox.SetSelection(0)
			profile.putPreference('color2_label', 'Generic')

	def RefreshColor(self):
		#print 'Refresh color'
		color_index = self.colorComboBox.GetSelection()
		color_label = self.colors[color_index].label
		profile.putPreference('color_label', color_label)
		filament_index = profile.getPreferenceInt('filament_index')
		fila = self.filaments[filament_index]
		if color_index > 0:
			filaments = self.configuration.getElementsByTagName("Filament")
			colors = filaments[filament_index].getElementsByTagName("Color")
			colors.sort(key=lambda color: _(color.getAttribute("name")))
			color = colors[color_index - 1]

			print_temperature_tags = color.getElementsByTagName("print_temperature")
			if len(print_temperature_tags) > 0:
				print_temperature = int(float(print_temperature_tags[0].firstChild.nodeValue))
			else:
				print_temperature = int(float(fila.print_temperature))
			if not self.temperatureSpinCtrl.IsEnabled():
				print_temperature += self.temp_preci
			self.temperatureSpinCtrl.SetValue(print_temperature)
			profile.putProfileSetting('print_temperature', str(print_temperature))

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
			print_temperature = int(float(fila.print_temperature))
			if not self.temperatureSpinCtrl.IsEnabled():
				print_temperature += self.temp_preci
			self.temperatureSpinCtrl.SetValue(print_temperature)
			profile.putProfileSetting('print_temperature', str(print_temperature))
			profile.putProfileSetting('filament_diameter', fila.filament_diameter)
			profile.putProfileSetting('filament_flow', fila.filament_flow)
			profile.putProfileSetting('retraction_speed', fila.retraction_speed)
			profile.putProfileSetting('retraction_amount', fila.retraction_amount)
			profile.putProfileSetting('filament_physical_density', fila.filament_physical_density)
			profile.putProfileSetting('filament_cost_kg', fila.filament_cost_kg)
			profile.putPreference('model_colour', fila.model_colour)

	def RefreshColor2(self):
		#print 'Refresh color'
		color_index = self.color2ComboBox.GetSelection()
		color_label = self.colors2[color_index].label
		profile.putPreference('color2_label', color_label)
		filament_index = profile.getPreferenceInt('filament2_index')
		fila = self.filaments[filament_index]
		if color_index > 0:
			filaments = self.configuration.getElementsByTagName("Filament")
			colors = filaments[filament_index].getElementsByTagName("Color")
			colors.sort(key=lambda color: _(color.getAttribute("name")))
			color = colors[color_index - 1]

			print_temperature_tags = color.getElementsByTagName("print_temperature")
			if len(print_temperature_tags) > 0:
				print_temperature = int(float(print_temperature_tags[0].firstChild.nodeValue))
			else:
				print_temperature = int(float(fila.print_temperature))
			if not self.temperature2SpinCtrl.IsEnabled():
				print_temperature += self.temp_preci
			self.temperature2SpinCtrl.SetValue(print_temperature)
			profile.putProfileSetting('print_temperature2', str(print_temperature))

			filament_diameter_tags = color.getElementsByTagName("filament_diameter")
			if len(filament_diameter_tags) > 0:
				filament_diameter = filament_diameter_tags[0].firstChild.nodeValue
			else:
				filament_diameter = fila.filament_diameter
			profile.putProfileSetting('filament_diameter2', str(filament_diameter))

			filament_flow_tags = color.getElementsByTagName("filament_flow")
			if len(filament_flow_tags) > 0:
				filament_flow = filament_flow_tags[0].firstChild.nodeValue
			else:
				filament_flow = fila.filament_flow
			profile.putProfileSetting('filament_flow2', str(filament_flow))

			retraction_speed_tags = color.getElementsByTagName("retraction_speed")
			if len(retraction_speed_tags) > 0:
				retraction_speed = retraction_speed_tags[0].firstChild.nodeValue
			else:
				retraction_speed = fila.retraction_speed
			profile.putProfileSetting('retraction_speed2', str(retraction_speed))

			retraction_amount_tags = color.getElementsByTagName("retraction_amount")
			if len(retraction_amount_tags) > 0:
				retraction_amount = retraction_amount_tags[0].firstChild.nodeValue
			else:
				retraction_amount = fila.retraction_amount
			profile.putProfileSetting('retraction_amount2', str(retraction_amount))

			filament_physical_density_tags = color.getElementsByTagName("filament_physical_density")
			if len(filament_physical_density_tags) > 0:
				filament_physical_density = filament_physical_density_tags[0].firstChild.nodeValue
			else:
				filament_physical_density = fila.filament_physical_density
			profile.putProfileSetting('filament_physical_density2', str(filament_physical_density))

			filament_cost_kg_tags = color.getElementsByTagName("filament_cost_kg")
			if len(filament_cost_kg_tags) > 0:
				filament_cost_kg = filament_cost_kg_tags[0].firstChild.nodeValue
			else:
				filament_cost_kg = fila.filament_cost_kg
			profile.putProfileSetting('filament_cost_kg2', str(filament_cost_kg))

			model_colour_tags = color.getElementsByTagName("model_colour")
			if len(model_colour_tags) > 0:
				model_colour = model_colour_tags[0].firstChild.nodeValue
			else:
				model_colour = fila.model_colour
			profile.putPreference('model_colour2', model_colour)
		else:
			print_temperature = int(float(fila.print_temperature))
			if not self.temperature2SpinCtrl.IsEnabled():
				print_temperature += self.temp_preci
			self.temperature2SpinCtrl.SetValue(print_temperature)
			profile.putProfileSetting('print_temperature2', str(print_temperature))
			profile.putProfileSetting('filament_diameter2', fila.filament_diameter)
			profile.putProfileSetting('filament_flow2', fila.filament_flow)
			profile.putProfileSetting('retraction_speed2', fila.retraction_speed)
			profile.putProfileSetting('retraction_amount2', fila.retraction_amount)
			profile.putProfileSetting('filament_physical_density2', fila.filament_physical_density)
			profile.putProfileSetting('filament_cost_kg2', fila.filament_cost_kg)
			profile.putPreference('model_colour2', fila.model_colour)

	def RefreshTemperatureSpinCtrl(self):
		#print 'Refresh Spin'
		profile.putProfileSetting('print_temperature', str(self.temperatureSpinCtrl.GetValue()))

	def RefreshTemperature2SpinCtrl(self):
		#print 'Refresh Spin'
		profile.putProfileSetting('print_temperature2', str(self.temperature2SpinCtrl.GetValue()))
	
	def RefreshStartExtruder(self):
		profile.putProfileSetting('start_extruder', self.extruders[self.startExtruderRadioBox.GetSelection()].value)

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
		new_temp_preci = int(float(preci.temp_preci))
		filament_index = profile.getPreferenceInt('filament_index')
		filament = self.filaments[filament_index]
		filament2_index = profile.getPreferenceInt('filament2_index')
		filament2 = self.filaments[filament2_index]
		if self.isSpecialFilament1():
			preci = filament
		if self.isSpecialFilament2():
			preci = filament2
		profile.putProfileSetting('layer_height', preci.layer_height)
		profile.putProfileSetting('solid_layer_thickness', preci.solid_layer_thickness)
		profile.putProfileSetting('wall_thickness', preci.wall_thickness)
		profile.putProfileSetting('print_speed', preci.print_speed)
		calculated_print_temperature = int(float(profile.getProfileSetting('print_temperature')))
		if not self.temperatureSpinCtrl.IsEnabled():
			calculated_print_temperature += new_temp_preci
			try:
				calculated_print_temperature -= self.temp_preci
			except:
				pass
		self.temperatureSpinCtrl.SetValue(calculated_print_temperature)
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			calculated_print_temperature2 = int(float(profile.getProfileSetting('print_temperature2')))
			if not self.temperature2SpinCtrl.IsEnabled():
				calculated_print_temperature2 += new_temp_preci
				try:
					calculated_print_temperature2 -= self.temp_preci
				except:
					pass
			self.temperature2SpinCtrl.SetValue(calculated_print_temperature2)
		self.temp_preci = new_temp_preci
		profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			profile.putProfileSetting('print_temperature2', str(calculated_print_temperature2))
		profile.putProfileSetting('travel_speed', preci.travel_speed)
		profile.putProfileSetting('bottom_layer_speed', preci.bottom_layer_speed)
		# Speed
		filament1_index = self.filamentComboBox.GetSelection()
		filament1_type = self.filaments[filament1_index].type.lower()
		filament2_type = ''
		try:
			filament2_index = self.filament2ComboBox.GetSelection()
			filament2_type = self.filaments[filament2_index].type.lower()
		except:
			pass
		if not 'support' in filament1_type and not 'support' in filament2_type:
			profile.putProfileSetting('infill_speed', preci.infill_speed)
			profile.putProfileSetting('inset0_speed', preci.inset0_speed)
			profile.putProfileSetting('insetx_speed', preci.insetx_speed)
		profile.putProfileSetting('solidarea_speed', preci.solidarea_speed)

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

	def RefreshSupport(self):
		supp = self.supports[self.supportRadioBox.GetSelection()]
		try:
			self.supportExtruderDualExtrusionRadioBox.Enable(supp.support != 'None')
		except:
			pass
		profile.putProfileSetting('support', supp.support)

	def RefreshSupportDualExtrusion(self):
		support_dual_extrusion_index = self.supportExtruderDualExtrusionRadioBox.GetSelection()
		profile.putPreference('support_dual_extrusion_index', support_dual_extrusion_index)
		suppDualExtrusion = self.support_dual_extrusions[support_dual_extrusion_index]
		profile.putProfileSetting('support_dual_extrusion', suppDualExtrusion.support_dual_extrusion)

	def RefreshWipeTowerVolume(self):
		wipe_tower_volume_index = self.wipeTowerVolumeRadioBox.GetSelection()
		profile.putPreference('wipe_tower_volume_index', wipe_tower_volume_index)
		wipeTowerVolume = self.wipe_tower_volumes[wipe_tower_volume_index]
		profile.putProfileSetting('wipe_tower_volume', wipeTowerVolume.wipe_tower_volume)

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
		printing_surface_name_index = self.printingSurfaceRadioBox.GetSelection()
		profile.putPreference('printing_surface_name_index', printing_surface_name_index)
		prtsurf = self.printing_surfaces[printing_surface_name_index]
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
	
	def OnStartExtruderRadioBoxChanged(self, event):
		self.RefreshStartExtruder()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnSupportRadioBoxChanged(self, event):
		self.RefreshSupport()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnSupportDualExtrusionRadioBoxChanged(self, event):
		self.RefreshSupportDualExtrusion()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def OnWipeTowerVolumeRadioBoxChanged(self, event):
		self.RefreshWipeTowerVolume()
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

	def OnFilament2ComboBoxChanged(self, event):
		self.RefreshFilament2()
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

	def OnColor2ComboBoxChanged(self, event):
		self.RefreshColor2()
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

	def OnTemperature2SpinCtrlChanged(self, event):
		self.RefreshTemperature2SpinCtrl()
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
