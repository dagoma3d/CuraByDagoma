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
from Cura.gui import expertConfig
from Cura.gui import alterationPanel
from Cura.gui import pluginPanel
from Cura.gui import pausePluginPanel
from Cura.gui import preferencesDialog
from Cura.gui import configWizard
from Cura.gui import firmwareInstall
from Cura.gui import simpleMode
from Cura.gui import sceneView
from Cura.gui import aboutWindow
from Cura.gui.util import dropTarget
from Cura.gui.tools import pidDebugger
from Cura.util import profile
from Cura.util import version
from Cura.util import meshLoader
from Cura.util import resources
from Cura.util import xmlconfig

class mainWindow(wx.Frame):
	def __init__(self):
		windowtitle = 'Cura by dagoma'
		try:
			windowtitle = windowtitle + ' ' + xmlConfig.getValue('Printer', 'machine_name')
		except:
			pass

		windowtitle = windowtitle + ' 1.0.7'

		super(mainWindow, self).__init__(None, title=windowtitle, pos=(0, 0), size=wx.DisplaySize())

		wx.EVT_CLOSE(self, self.OnClose)

		# allow dropping any file, restrict later
		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles))

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO) #MOI Ajoute Icone dagoma.ico
		self.SetIcon(frameicon)

		# TODO: wxWidgets 2.9.4 has a bug when NSView does not register for dragged types when wx drop target is set. It was fixed in 2.9.5
		if sys.platform.startswith('darwin'):
			try:
				import objc
				nswindow = objc.objc_object(c_void_p=self.MacGetTopLevelWindowRef())
				view = nswindow.contentView()
				view.registerForDraggedTypes_([u'NSFilenamesPboardType'])
			except:
				pass

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		appname = 'Cura by Dagoma'
		if 'printername' in locals():
			appname = appname + ' ' + printername
		self.config = wx.FileConfig(appName=appname,
						localFilename=mruFile,
						style=wx.CONFIG_USE_LOCAL_FILE)

		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in xrange(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in xrange(10)]
		self.profileFileHistory = wx.FileHistory(10, self.ID_MRU_PROFILE1)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Load(self.config)

		self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, _("Open an Object") + "\tCTRL+L")
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showLoadModel(), i)
		i = self.fileMenu.Append(1, _("Prepare the Print") + "\tCTRL+S")
		self.Bind(wx.EVT_MENU, self.OnPreparePrint, i)
		i = self.fileMenu.Append(-1, _("Preferences") + "...\tCTRL+P")
		self.Bind(wx.EVT_MENU, self.OnLanguagePreferences, i)

		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), '&' + _("Recently Opened Objects"), modelHistoryMenu)
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, _("Quit"))
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menubar.Append(self.fileMenu, _("File"))

		language = profile.getPreference("language")
		if language == "French":
			contact_url = "https://dagoma.fr/heroes/diagnostique-en-ligne.html"
			buy_url = "https://dagoma.fr/boutique/filaments.html"
		else:
			contact_url = "https://dagoma3d.com/pages/contact-us"
			buy_url = "https://dagoma3d.com/collections/shop"

		self.helpMenu = wx.Menu()
		i = self.helpMenu.Append(-1, _("Contact us"))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(contact_url), i)
		i = self.helpMenu.Append(-1, _("Buy filament"))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(buy_url), i)
		i = self.helpMenu.Append(-1, _("About"))
		self.Bind(wx.EVT_MENU, self.OnAbout, i)
		self.menubar.Append(self.helpMenu, _("Help"))

		self.SetMenuBar(self.menubar)

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3D | wx.SP_LIVE_UPDATE)
		self.viewPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		#self.optionsPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.optionsPane = scrolledpanel.ScrolledPanel(self.splitter, style=wx.BORDER_NONE)
		self.optionsPane.SetupScrolling(True, True)
		self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		##Gui components##
		self.normalSettingsPanel = normalSettingsPanel(self.optionsPane, lambda : self.scene.sceneUpdated())

		self.optionsSizer = wx.BoxSizer(wx.VERTICAL)
		self.optionsSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.optionsPane.SetSizer(self.optionsSizer)

		#Preview window
		self.scene = sceneView.SceneView(self.viewPane)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.viewPane.SetSizer(sizer)
		sizer.Add(self.scene, 1, flag=wx.EXPAND)

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		sizer.Layout()
		self.sizer = sizer

		self.updateProfileToAllControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		self.normalSettingsPanel.Show()

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2, wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()
		self.Maximize(True)

		self.SetMinSize((800, 600))
		self.splitter.SplitVertically(self.viewPane, self.optionsPane, int(profile.getPreference('window_normal_sash')))
		self.splitter.SetSashGravity(1.0) # Only the SceneView is resized when the windows size is modifed

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800, 600))
			self.Centre()

		self.optionsPane.SetMinSize((310, 600))
		self.optionsPane.Layout()
		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()
		self.scene.SetFocus()

	def OnLanguagePreferences(self, e):
		prefDialog = preferencesDialog.languagePreferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()
		wx.CallAfter(prefDialog.Show)

	def OnPreparePrint(self, e):
		profile.printSlicingInfo()
		self.scene.OnPrintButton(1)
		e.Skip()

	def OnDropFiles(self, files):
		if len(files) > 0:
			self.updateProfileToAllControls()
		self.scene.loadFiles(files)

	def addToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()

	def addToModelMRU(self, file):
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
		self.updateProfileToAllControls()

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

	def updateProfileToAllControls(self):
		self.scene.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()

	def OnAbout(self, e):
		aboutBox = aboutWindow.aboutWindow()
		aboutBox.Centre()
		aboutBox.Show()

	def OnClose(self, e):
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		profile.putPreference('window_normal_sash', '-' + str(self.optionsPane.GetSize()[0]))

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

	class Remplissage:
		def __init__(self):
			self.type = ''
			self.fill_density = ''

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

	class Tete:
		def __init__(self):
			self.type = ''
			self.fan_speed = ''
			self.cool_min_layer_time = ''

	class Support:
		def __init__(self):
			self.support = None

	class Brim:
		def __init__(self):
			self.platform_adhesion = None

	class Palpeur:
		def __init__(self):
			self.palpeur = None

	def __init__(self, parent, callback = None):
		super(normalSettingsPanel, self).__init__(parent, callback)
		self.already_loaded = False
		self.parent = parent
		self.loadxml()
		self.label_1 = wx.StaticText(self, wx.ID_ANY, _("Filament"))
		self.warning_text = wx.StaticText(self, wx.ID_ANY, _("Warning text"))
		warning_text_font = self.warning_text.GetFont()
		warning_text_font.SetPointSize(10)
		warning_text_font.SetWeight(wx.FONTWEIGHT_BOLD)
		self.warning_text.SetFont(warning_text_font)
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.color_box = wx.Choice(self, wx.ID_ANY, choices = [])
		else:
			self.color_box = wx.ComboBox(self, wx.ID_ANY, choices = [] , style=wx.CB_DROPDOWN | wx.CB_READONLY)

		self.label_4 = wx.StaticText(self, wx.ID_ANY, _(("Temperature (°C) :").decode('utf-8')))
		self.spin_ctrl_1 = wx.SpinCtrl(self, wx.ID_ANY, profile.getProfileSetting('print_temperature'), min=175, max=255, style=wx.SP_ARROW_KEYS | wx.TE_AUTO_URL)
		self.button_1 = wx.Button(self, wx.ID_ANY, _("Prepare the Print"))
		# Pause plugin
		self.pausePluginButton = wx.Button(self, wx.ID_ANY, _(("Color change(s)")))
		self.pausePluginPanel = pausePluginPanel.pausePluginPanel(self, callback)
		self.__set_properties()
		self.__do_layout()


		self.Init_Palpeur_chbx()
		#Refresh ALL Value
		self.Refresh_Supp()
		self.Refresh_Preci()
		self.Refresh_Tet()
		self.Refresh_Fila()
		self.Refresh_Color()
		self.Refresh_SpinCtrl()
		self.Refresh_Rempli()
		self.Refresh_Palpeur_chbx()
		self.Refresh_Checkboxbrim()

		profile.saveProfile(profile.getDefaultProfilePath(), True)

		#Evt Select Filament
		if sys.platform == 'darwin':
			self.Bind(wx.EVT_CHOICE, self.EVT_Fila, self.combo_box_1)
			self.Bind(wx.EVT_CHOICE, self.EVT_Color, self.color_box)
		else:
			self.Bind(wx.EVT_COMBOBOX, self.EVT_Fila, self.combo_box_1)
			self.Bind(wx.EVT_COMBOBOX, self.EVT_Color, self.color_box)

		self.Bind(wx.EVT_TEXT, self.EVT_SpinCtrl, self.spin_ctrl_1)
		self.Bind(wx.EVT_TEXT_ENTER, self.EVT_SpinCtrl, self.spin_ctrl_1)
		self.Bind(wx.EVT_SPINCTRL, self.EVT_SpinCtrl, self.spin_ctrl_1)
		self.Bind(wx.EVT_RADIOBOX, self.EVT_Preci, self.radio_box_1)
		self.Bind(wx.EVT_RADIOBOX, self.EVT_Tet, self.tetes_box)
		self.Bind(wx.EVT_RADIOBOX, self.EVT_Supp, self.printsupp)
		self.Bind(wx.EVT_RADIOBOX, self.EVT_Rempl, self.radio_box_2)
		self.Bind(wx.EVT_CHECKBOX, self.EVT_Checkboxpalpeur,self.palpeur_chbx)
		self.Bind(wx.EVT_CHECKBOX, self.EVT_Supp ,self.printsupp)
		self.Bind(wx.EVT_CHECKBOX, self.EVT_Checkboxbrim, self.printbrim)
		self.Bind(wx.EVT_BUTTON, self.ClickPreparePrintButton, self.button_1)
		self.Bind(wx.EVT_BUTTON, self.ClickPauseButton, self.pausePluginButton)
 		#self.Bind(wx.EVT_SIZE, self.OnSize)


	def __set_properties(self):
		self.spin_ctrl_1.Enable(False)
		self.printsupp.SetSelection(0)


	def __do_layout(self):
		printername = profile.getMachineSetting('machine_name')
		if printername == "Neva":
			self.tetes_box.Hide()
			self.palpeur_chbx.Hide()
		if printername == "Explorer350":
			self.tetes_box.Hide()
		self.pausePluginButton.Hide()

		language = profile.getPreference("language")
		if language == "French":
			url = "https://dagoma.fr/boutique/filaments.html"
		else:
			url = "https://dagoma3d.com/collections/shop"

		self.buylink = hl.HyperLinkCtrl(self, wx.ID_ANY, _("Buy filament"), URL=url)

		filament_sizer = wx.GridBagSizer(0, 3)
		filament_sizer.Add(self.label_1, pos=(0, 0), flag = wx.LEFT|wx.TOP, border = 0)
		filament_sizer.Add(wx.StaticText(self, wx.ID_ANY, " ("), pos=(0, 1), flag = wx.LEFT|wx.TOP, border = 0)
		filament_sizer.Add(self.buylink, pos=(0, 2), flag = wx.LEFT|wx.TOP, border = 0)
		filament_sizer.Add(wx.StaticText(self, wx.ID_ANY, "):"), pos=(0, 3), flag = wx.LEFT|wx.TOP, border = 0)

		if printername == "DiscoEasy200":
			sizer_1 = wx.GridBagSizer(15, 0)
			sizer_1.SetEmptyCellSize((0, 0))
			sizer_1.Add(filament_sizer, pos=(0, 0), flag = wx.LEFT|wx.TOP, border = 5)
			sizer_1.Add(self.combo_box_1, pos = (1, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.color_box, pos = (2, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.warning_text, pos=(3, 0), flag = wx.LEFT|wx.TOP, border = 5)
			sizer_1.Add(self.label_4, pos = (4, 0), flag = wx.LEFT|wx.TOP,  border = 5)
			sizer_1.Add(self.spin_ctrl_1, pos = (5, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.radio_box_2, pos = (6, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.radio_box_1, pos = (7, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.tetes_box, pos = (8, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.printsupp, pos = (9, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.palpeur_chbx, pos = (10, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.printbrim, pos = (11, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.pausePluginButton, pos = (12, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.pausePluginPanel, pos = (13, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.button_1, pos = (14, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add((0, 15), pos = (15, 0))
		elif printername == "Neva":
			sizer_1 = wx.GridBagSizer(13, 0)
			sizer_1.SetEmptyCellSize((0, 0))
			sizer_1.Add(filament_sizer, pos=(0, 0), flag = wx.LEFT|wx.TOP, border = 5)
			sizer_1.Add(self.combo_box_1, pos = (1, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.color_box, pos = (2, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.warning_text, pos=(3, 0), flag = wx.LEFT|wx.TOP, border = 5)
			sizer_1.Add(self.label_4, pos = (4, 0), flag = wx.LEFT|wx.TOP,  border = 5)
			sizer_1.Add(self.spin_ctrl_1, pos = (5, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.radio_box_2, pos = (6, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.radio_box_1, pos = (7, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.printsupp, pos = (8, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.printbrim, pos = (9, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.pausePluginButton, pos = (10, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.pausePluginPanel, pos = (11, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.button_1, pos = (12, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add((0, 15), pos = (13, 0))
		elif printername == "Explorer350":
			sizer_1 = wx.GridBagSizer(14, 0)
			sizer_1.SetEmptyCellSize((0, 0))
			sizer_1.Add(filament_sizer, pos=(0, 0), flag = wx.LEFT|wx.TOP, border = 5)
			sizer_1.Add(self.combo_box_1, pos = (1, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.color_box, pos = (2, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.warning_text, pos=(3, 0), flag = wx.LEFT|wx.TOP, border = 5)
			sizer_1.Add(self.label_4, pos = (4, 0), flag = wx.LEFT|wx.TOP,  border = 5)
			sizer_1.Add(self.spin_ctrl_1, pos = (5, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.radio_box_2, pos = (6, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.radio_box_1, pos = (7, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.printsupp, pos = (8, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.palpeur_chbx, pos = (9, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.printbrim, pos = (10, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.pausePluginButton, pos = (11, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.pausePluginPanel, pos = (12, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add(self.button_1, pos = (13, 0), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
			sizer_1.Add((0, 15), pos = (14, 0))

		if sizer_1 is not None:
			sizer_1.AddGrowableCol(0)
			self.SetSizerAndFit(sizer_1)
		self.Layout()

	def loadxml(self):
		self.init_Printer()
		self.init_Configuration()
		self.get_filaments()
		self.get_remplissage()
		self.get_Precision()
		self.get_Tete()
		self.get_support()
		self.get_brim()
		self.get_palpeur()

	def setProfileSetting(self, sub, var):
		value = xmlconfig.getValue(var, sub)
		if value is not None:
			profile.putProfileSetting(var, value)

	def setPreferenceSetting(self, sub, var):
		value = xmlconfig.getValue(var, sub)
		if value is not None:
			profile.putPreference(var, value)

	def setMachineSetting(self, sub, var):
		value = xmlconfig.getValue(var, sub)
		if value is not None:
			profile.putMachineSetting(var, value)

	def init_Printer(self):
		printer = xmlconfig.getTag('Printer')
		self.setMachineSetting(printer, 'machine_name')
		self.setMachineSetting(printer, 'machine_type')
		self.setMachineSetting(printer, 'machine_width')
		self.setMachineSetting(printer, 'machine_depth')
		self.setMachineSetting(printer, 'machine_height')
		self.setMachineSetting(printer, 'extruder_amount')
		self.setMachineSetting(printer, 'has_heated_bed')
		self.setMachineSetting(printer, 'machine_center_is_zero')
		self.setMachineSetting(printer, 'machine_shape')
		self.setMachineSetting(printer, 'extruder_head_size_min_x')
		self.setMachineSetting(printer, 'extruder_head_size_min_y')
		self.setMachineSetting(printer, 'extruder_head_size_max_x')
		self.setMachineSetting(printer, 'extruder_head_size_max_y')
		self.setMachineSetting(printer, 'extruder_head_size_height')
		self.setProfileSetting(printer, 'nozzle_size')
		self.setProfileSetting(printer, 'retraction_enable')

	def init_Configuration(self):
		global_config = xmlconfig.getTag('Configuration')
		if global_config is not None:
			config = global_config
		else:
			config = xmlconfig.getTag('Config_Adv')

		self.setProfileSetting(config, 'bottom_thickness')
		self.setProfileSetting(config, 'layer0_width_factor')
		self.setProfileSetting(config, 'object_sink')
		self.setProfileSetting(config, 'fan_enabled')

		if global_config is not None:
			config = global_config
		else:
			config = xmlconfig.getTag('Config_Expert')
		# Retraction
		self.setProfileSetting(config, 'retraction_min_travel')
		self.setProfileSetting(config, 'retraction_combing')
		self.setProfileSetting(config, 'retraction_minimal_extrusion')
		self.setProfileSetting(config, 'retraction_hop')
		# Skirt
		self.setProfileSetting(config, 'skirt_line_count')
		self.setProfileSetting(config, 'skirt_gap')
		self.setProfileSetting(config, 'skirt_minimal_length')
		# Cool
		self.setProfileSetting(config, 'fan_full_height')
		#self.setProfileSetting(config, 'fan_speed')
		self.setProfileSetting(config, 'fan_speed_max')
		self.setProfileSetting(config, 'cool_min_feedrate')
		self.setProfileSetting(config, 'cool_head_lift')
		# Infill
		self.setProfileSetting(config, 'solid_top')
		self.setProfileSetting(config, 'solid_bottom')
		self.setProfileSetting(config, 'fill_overlap')
		# Support
		self.setProfileSetting(config, 'support_type')
		self.setProfileSetting(config, 'support_angle')
		self.setProfileSetting(config, 'support_fill_rate')
		self.setProfileSetting(config, 'support_xy_distance')
		self.setProfileSetting(config, 'support_z_distance')
		# Block Magic
		self.setProfileSetting(config, 'spiralize')
		self.setProfileSetting(config, 'simple_mode')
		# Brim
		self.setProfileSetting(config, 'brim_line_count')
		# Raft
		self.setProfileSetting(config, 'raft_margin')
		self.setProfileSetting(config, 'raft_line_spacing')
		self.setProfileSetting(config, 'raft_base_thickness')
		self.setProfileSetting(config, 'raft_base_linewidth')
		self.setProfileSetting(config, 'raft_interface_thickness')
		self.setProfileSetting(config, 'raft_interface_linewidth')
		self.setProfileSetting(config, 'raft_airgap')
		self.setProfileSetting(config, 'raft_surface_layers')
		# Fix Horrible
		self.setProfileSetting(config, 'fix_horrible_union_all_type_a')
		self.setProfileSetting(config, 'fix_horrible_union_all_type_b')
		self.setProfileSetting(config, 'fix_horrible_use_open_bits')
		self.setProfileSetting(config, 'fix_horrible_extensive_stitching')

		if global_config is not None:
			config = global_config
		else:
			config = xmlconfig.getTag('Config_Preferences')
		# Colors
		self.setPreferenceSetting(config, 'model_colour')
		#Cura Settings
		self.setPreferenceSetting(config, 'auto_detect_sd')

	def get_filaments(self):
		filaments = xmlconfig.getTags('Filament')
		self.filaments = []
		choices = []
		for filament in filaments:
			if filament.hasAttributes():
				fila = self.Filament()
				name = filament.getAttribute("name")
				choices.append(_(name))
				fila.type = name
			try :
				if xmlconfig.getTag("grip_temperature", filament) is not None:
					fila.grip_temperature = xmlconfig.getValue("grip_temperature", filament)
				else:
					fila.grip_temperature = xmlconfig.getValue("print_temperature", filament)
				fila.print_temperature = xmlconfig.getValue("print_temperature", filament)
				fila.filament_diameter = xmlconfig.getValue("filament_diameter", filament)
				fila.filament_flow = xmlconfig.getValue("filament_flow", filament)
				fila.retraction_speed = xmlconfig.getValue("retraction_speed", filament)
				fila.retraction_amount = xmlconfig.getValue("retraction_amount", filament)
				fila.filament_physical_density = xmlconfig.getValue("filament_physical_density", filament)
				fila.filament_cost_kg = xmlconfig.getValue("filament_cost_kg", filament)
				self.filaments.append(fila)
			except:
				print 'Some Error in Filament Bloc'
				pass

		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.combo_box_1 = wx.Choice(self, wx.ID_ANY, choices = choices)
		else:
			self.combo_box_1 = wx.ComboBox(self, wx.ID_ANY, choices = choices , style=wx.CB_DROPDOWN | wx.CB_READONLY)
		self.combo_box_1.SetSelection(int(profile.getPreference('filament_index')))

	def get_remplissage(self):
		bloc_name = _("Filling density :")
		remplissages = xmlconfig.getTags("Filling")
		if len(remplissages) == 0:
			remplissages = xmlconfig.getTags("Remplissage")
		choices = []
		self.remplissages = []
		for remplissage in remplissages:
			if remplissage.hasAttributes():
				rempli = self.Remplissage()
				name = _(remplissage.getAttribute("name"))
				choices.append(name)
				rempli.type = name
				try :
					rempli.fill_density = xmlconfig.getValue("fill_density", remplissage)
					self.remplissages.append(rempli)
				except:
					print 'Some Errors in Remplissage Bloc'
					pass
		self.radio_box_2 = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices = choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.radio_box_2.SetSelection(int(profile.getPreference('fill_index')))

	def get_Precision(self):
		bloc_name = _("Quality (layer thickness) :")
		precisions = xmlconfig.getTags("Precision")
		choices = []
		self.precisions = []
		for precision in precisions:
			if precision.hasAttributes():
				preci = self.Precision()
				name = precision.getAttribute("name")
				choices.append(_(name))
				preci.type = name
				try :
					preci.layer_height = xmlconfig.getValue("layer_height", precision)
					preci.solid_layer_thickness = xmlconfig.getValue("solid_layer_thickness", precision)
					preci.wall_thickness = xmlconfig.getValue("wall_thickness", precision)
					preci.print_speed = xmlconfig.getValue("print_speed", precision)
					preci.temp_preci = xmlconfig.getValue("temp_preci", precision)
					preci.travel_speed = xmlconfig.getValue("travel_speed", precision)
					preci.bottom_layer_speed = xmlconfig.getValue("bottom_layer_speed", precision)
					preci.infill_speed = xmlconfig.getValue("infill_speed", precision)
					preci.inset0_speed = xmlconfig.getValue("inset0_speed", precision)
					preci.insetx_speed = xmlconfig.getValue("insetx_speed", precision)
					self.precisions.append(preci)
				except :
					print 'Some Error in Precision Bloc'
					pass
		self.radio_box_1 = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.radio_box_1.SetSelection(int(profile.getPreference('precision_index')))

	def get_Tete(self):
		bloc_name = _("Printhead version :")
		tetes = xmlconfig.getTags("PrinterHead")
		if len(tetes) == 0:
			tetes = xmlconfig.getTags("Tete")
		choices = []
		self.tetes = []
		for tete in tetes:
			if tete.hasAttributes():
				tet = self.Tete()
				name = tete.getAttribute("name")
				choices.append(_(name))
				tet.type = name
				try :
					tet.fan_speed = xmlconfig.getValue("fan_speed", tete)
					tet.cool_min_layer_time = xmlconfig.getValue("cool_min_layer_time", tete)
					self.tetes.append(tet)
				except :
					print 'Some Error in Tete Bloc'
					pass
		self.tetes_box = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.tetes_box.SetSelection(int(profile.getPreference('printhead_index')))

	def get_support(self):
		bloc_name = _("Printing supports :")
		supports = xmlconfig.getTags("Support")
		choices = []
		self.supports = []
		for support in supports:
			if support.hasAttributes():
				supp = self.Support()
				name = _(support.getAttribute("name"))
				choices.append(name)
				supp.type = name
				try :
					supp.support = xmlconfig.getValue("support", support)
					self.supports.append(supp)
				except :
					print 'Some Error in Supports Bloc'
					pass
		self.printsupp = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

	def get_brim(self):
		bloc_name = _("Improve the adhesion surface")
		self.printbrim = wx.CheckBox(self, wx.ID_ANY, bloc_name)
		brim_enable = xmlconfig.getTag("Brim_Enable")
		brim_disable = xmlconfig.getTag("Brim_Disable")
		self.brims = []
		self.brims.append(self.Brim())
		self.brims[0].platform_adhesion = xmlconfig.getValue("platform_adhesion", brim_enable)
		self.brims.append(self.Brim())
		self.brims[1].platform_adhesion = xmlconfig.getValue("platform_adhesion", brim_disable)

	# Fonction qui recupere dans le xml les differentes lignes pour le bloc Palpeur
	def get_palpeur(self):
		bloc_name = _("Use the sensor")
		self.palpeur_chbx = wx.CheckBox(self, wx.ID_ANY, bloc_name)
		palpeur_enable = xmlconfig.getTags("Sensor_Enable")
		if len(palpeur_enable) == 0:
			palpeur_enable = xmlconfig.getTags("Palpeur_Enable")
			sensor_enabled = xmlconfig.getValue("palpeur", palpeur_enable[0])
		else:
			sensor_enabled = xmlconfig.getValue("value", palpeur_enable[0])
		palpeur_disable = xmlconfig.getTags("Sensor_Disable")
		if len(palpeur_disable) == 0:
			palpeur_disable = xmlconfig.getTags("Palpeur_Disable")
			sensor_disabled = xmlconfig.getValue("palpeur", palpeur_disable[0])
		else:
			sensor_disabled = xmlconfig.getValue("value", palpeur_disable[0])
		self.palpeurs = []
		self.palpeurs.append(self.Palpeur())
		self.palpeurs[0].palpeur = sensor_enabled
		self.palpeurs.append(self.Palpeur())
		self.palpeurs[1].palpeur = sensor_disabled

	def Refresh_Fila(self):
		#print "Refresh fila"
		filament_index = self.combo_box_1.GetSelection()
		fila = self.filaments[filament_index]
		profile.putPreference('filament_index', filament_index)
		profile.putProfileSetting('grip_temperature', fila.grip_temperature)
		calculated_print_temperature = float(fila.print_temperature)
		if fila.type == 'Other PLA type' or fila.type == 'Autre PLA':
			self.warning_text.SetLabel(_("This setting must be used with caution!"))
			self.warning_text.SetForegroundColour((169, 68, 66))
			self.spin_ctrl_1.Enable(True)
		else:
			calculated_print_temperature += self.temp_preci
			self.warning_text.SetLabel(_("Filament approved by Dagoma."))
			self.warning_text.SetForegroundColour((60, 118, 61))
			self.spin_ctrl_1.Enable(False)
		profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
		self.spin_ctrl_1.SetValue(calculated_print_temperature)
		profile.putProfileSetting('filament_diameter', fila.filament_diameter)
		profile.putProfileSetting('filament_flow', fila.filament_flow)
		profile.putProfileSetting('retraction_speed', fila.retraction_speed)
		profile.putProfileSetting('retraction_amount', fila.retraction_amount)
		profile.putProfileSetting('filament_physical_density', fila.filament_physical_density)
		profile.putProfileSetting('filament_cost_kg', fila.filament_cost_kg)

		self.color_box.Clear()
		self.color_box.Append(_("Generic"))
		filaments = xmlconfig.getTags("Filament")
		colors = xmlconfig.getTags("Color", filaments[filament_index])
		if len(colors) > 0:
			self.color_box.Enable(True)
			for color in colors:
				if color.hasAttributes():
					name = _(color.getAttribute("name"))
					self.color_box.Append(name)
		else:
			self.color_box.Enable(False)

		if not self.already_loaded:
			color_index = int(profile.getPreference('color_index')) + 1
			self.color_box.SetSelection(color_index)
			self.already_loaded = True
		else:
			self.color_box.SetSelection(0)
			profile.putPreference('color_index', -1)

	def Refresh_Color(self):
		#print 'Refresh color'
		color_index = self.color_box.GetSelection() - 1
		profile.putPreference('color_index', color_index)
		filament_index = int(profile.getPreference('filament_index'))
		if color_index > -1:
			filaments = xmlconfig.getTags("Filament")
			colors = filaments[filament_index].getElementsByTagName("Color")
			color = colors[color_index]

			print_temperature = xmlconfig.getValue("print_temperature", color)
			if print_temperature is not None:
				calculated_print_temperature = float(print_temperature)
				if not self.spin_ctrl_1.IsEnabled():
					calculated_print_temperature += self.temp_preci
				self.spin_ctrl_1.SetValue(calculated_print_temperature)
				profile.putProfileSetting('print_temperature', str(calculated_print_temperature))

			self.setProfileSetting(color, 'grip_temperature')
			self.setProfileSetting(color, 'filament_diameter')
			self.setProfileSetting(color, 'filament_flow')
			self.setProfileSetting(color, 'retraction_speed')
			self.setProfileSetting(color, 'retraction_amount')
			self.setProfileSetting(color, 'filament_physical_density')
			self.setProfileSetting(color, 'filament_cost_kg')
		else:
			fila = self.filaments[filament_index]
			calculated_print_temperature = float(fila.print_temperature)
			if not self.spin_ctrl_1.IsEnabled():
				calculated_print_temperature += self.temp_preci
			self.spin_ctrl_1.SetValue(calculated_print_temperature)
			profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
			profile.putProfileSetting('grip_temperature', fila.grip_temperature)
			profile.putProfileSetting('filament_diameter', fila.filament_diameter)
			profile.putProfileSetting('filament_flow', fila.filament_flow)
			profile.putProfileSetting('retraction_speed', fila.retraction_speed)
			profile.putProfileSetting('retraction_amount', fila.retraction_amount)
			profile.putProfileSetting('filament_physical_density', fila.filament_physical_density)
			profile.putProfileSetting('filament_cost_kg', fila.filament_cost_kg)

	def Refresh_SpinCtrl(self):
		#print 'Refresh Spin'
		profile.putProfileSetting('print_temperature', str(self.spin_ctrl_1.GetValue()))

	def Refresh_Rempli(self):
		fill_index = self.radio_box_2.GetSelection()
		rempli = self.remplissages[fill_index]
		profile.putPreference('fill_index', fill_index)
		profile.putProfileSetting('fill_density', rempli.fill_density)

	def Refresh_Preci(self):
		precision_index = self.radio_box_1.GetSelection()
		preci = self.precisions[precision_index]
		profile.putPreference('precision_index', precision_index)
		profile.putProfileSetting('layer_height', preci.layer_height)
		profile.putProfileSetting('solid_layer_thickness', preci.solid_layer_thickness)
		profile.putProfileSetting('wall_thickness', preci.wall_thickness)
		profile.putProfileSetting('print_speed', preci.print_speed)
		new_temp_preci = float(preci.temp_preci)
		calculated_print_temperature = float(profile.getProfileSetting('print_temperature'))
		if not self.spin_ctrl_1.IsEnabled():
			calculated_print_temperature += new_temp_preci
			try:
				calculated_print_temperature -= self.temp_preci
			except:
				pass
		self.temp_preci = new_temp_preci
		self.spin_ctrl_1.SetValue(calculated_print_temperature)
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

	def Refresh_Tet(self):
		printhead_index = self.tetes_box.GetSelection()
		tet = self.tetes[printhead_index]
		profile.putPreference('printhead_index', printhead_index)
		profile.putProfileSetting('fan_speed', tet.fan_speed)
		profile.putProfileSetting('cool_min_layer_time', tet.cool_min_layer_time)

	def Refresh_Supp(self):
		supp = self.supports[self.printsupp.GetSelection()]
		profile.putProfileSetting('support', supp.support)

	def Refresh_Checkboxbrim(self):
		if self.printbrim.GetValue():
			profile.putProfileSetting('platform_adhesion', self.brims[0].platform_adhesion)
		else:
			profile.putProfileSetting('platform_adhesion', self.brims[1].platform_adhesion)

	# fonction pour initialiser la checkbox palpeur dans le profil
	def Init_Palpeur_chbx(self):
		if profile.getProfileSetting('palpeur_enable') == 'Palpeur' or profile.getProfileSetting('palpeur_enable') == 'Enabled':
			self.palpeur_chbx.SetValue(True)
		else :
			self.palpeur_chbx.SetValue(False)
		self.palpeur_chbx.Refresh()

	# fonction pour enregistrer les données relative au palpeur dans le profil
	def Refresh_Palpeur_chbx(self):
		if self.palpeur_chbx.GetValue():
			sensor_value = self.palpeurs[0].palpeur
		else:
			sensor_value = self.palpeurs[1].palpeur
		profile.putProfileSetting('palpeur_enable', sensor_value)

	def EVT_Supp(self, event):
		self.Refresh_Supp()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_Checkboxbrim(self, event):
		self.Refresh_Checkboxbrim()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_Preci(self, event):
		self.Refresh_Preci()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_Tet(self, event):
		self.Refresh_Tet()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_Rempl(self, event):
		self.Refresh_Rempli()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_Fila(self, event):
		self.Refresh_Fila()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_Color(self, event):
		self.Refresh_Color()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	def EVT_SpinCtrl(self, event):
		self.Refresh_SpinCtrl()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	# evenement sur le bloc palpeur
	def EVT_Checkboxpalpeur(self, event):
		self.Refresh_Palpeur_chbx()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()


	def ClickPreparePrintButton(self, event):
		profile.printSlicingInfo()
		self.GetParent().GetParent().GetParent().scene.OnPrintButton(1)
		event.Skip()

	def ClickPauseButton(self, event):
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
