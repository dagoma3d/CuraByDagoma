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
from xml.dom import minidom

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

doc = minidom.parse(resources.getPathForXML('xml_config.xml'))

class mainWindow(wx.Frame):
	def __init__(self):
		windowtitle = 'Cura by dagoma'
		try:
			printerinfo = doc.getElementsByTagName("Printer")[0];
			printername = printerinfo.getElementsByTagName("machine_name")[0].childNodes[0].data
			windowtitle = windowtitle + ' ' + printername
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
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveGCode(), i)
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
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2,wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()

		# Restore the window position, size & state from the preferences file
		try:
			if profile.getPreference('window_maximized') == 'True':
				self.Maximize(True)
			else:
				posx = int(profile.getPreference('window_pos_x'))
				posy = int(profile.getPreference('window_pos_y'))
				width = int(profile.getPreference('window_width'))
				height = int(profile.getPreference('window_height'))
				if posx > 0 or posy > 0:
					self.SetPosition((posx,posy))
				if width > 0 and height > 0:
					self.SetSize((width,height))
		except:
			self.Maximize(True)

		self.SetMinSize((800, 600))
		self.splitter.SplitVertically(self.viewPane, self.optionsPane)
		self.splitter.SetSashGravity(1.0) # Only the SceneView is resized when the windows size is modifed
		self.splitter.SetSashSize(4) # Enabled sash

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800, 600))
			self.Centre()

		self.optionsPane.Layout()
		self.optionsPane.SetMinSize((390, 600))
		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()
		self.scene.SetFocus()

	def OnLanguagePreferences(self, e):
		prefDialog = preferencesDialog.languagePreferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()
		wx.CallAfter(prefDialog.Show)

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

		# Save the window position, size & state from the preferences file
		profile.putPreference('window_maximized', self.IsMaximized())
		if not self.IsMaximized() and not self.IsIconized():
			(posx, posy) = self.GetPosition()
			profile.putPreference('window_pos_x', posx)
			profile.putPreference('window_pos_y', posy)
			(width, height) = self.GetSize()
			profile.putPreference('window_width', width)
			profile.putPreference('window_height', height)

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
		self.Bind(wx.EVT_BUTTON, self.Click_Button, self.button_1)
		self.Bind(wx.EVT_BUTTON, self.ClickPauseButton, self.pausePluginButton)
 		#self.Bind(wx.EVT_SIZE, self.OnSize)


	def __set_properties(self):
		self.spin_ctrl_1.Enable(False)
		self.printsupp.SetSelection(0)


	def __do_layout(self):
		printerinfo = doc.getElementsByTagName("Printer")[0];
		printername = printerinfo.getElementsByTagName("machine_name")[0].childNodes[0].data
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

	def getNodeText(self, node):
		nodelist = node.childNodes
		result = []
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				result.append(node.data)
		return ''.join(result)

	def loadxml(self):
		self.get_filaments()
		self.get_remplissage()
		self.get_Precision()
		self.get_Tete()
		self.get_support()
		self.get_brim()
		self.get_palpeur()
		self.init_Config_Preferences()
		self.init_Config_Adv()
		self.init_Config_Expert()

	def setvalue_from_xml(self, sub, var):
		profile.putProfileSetting(var, self.getNodeText(sub.getElementsByTagName(var)[0]))

	def setvalue_from_xml_pref(self, sub, var):
		profile.putPreference(var, self.getNodeText(sub.getElementsByTagName(var)[0]))

	def init_Config_Adv(self):
		config_adv = doc.getElementsByTagName("Config_Adv")[0]
		self.setvalue_from_xml(config_adv, 'bottom_thickness')
		self.setvalue_from_xml(config_adv, 'layer0_width_factor')
		self.setvalue_from_xml(config_adv, 'object_sink')
		self.setvalue_from_xml(config_adv, 'fan_enabled')
		print 'Config_Adv Reload from XML file'

	def init_Config_Expert(self):
		config_expert = doc.getElementsByTagName("Config_Expert")[0]
		# Retraction
		self.setvalue_from_xml(config_expert, 'retraction_min_travel')
		self.setvalue_from_xml(config_expert, 'retraction_combing')
		self.setvalue_from_xml(config_expert, 'retraction_minimal_extrusion')
		self.setvalue_from_xml(config_expert, 'retraction_hop')
		# Skirt
		self.setvalue_from_xml(config_expert, 'skirt_line_count')
		self.setvalue_from_xml(config_expert, 'skirt_gap')
		self.setvalue_from_xml(config_expert, 'skirt_minimal_length')
		# Cool
		self.setvalue_from_xml(config_expert, 'fan_full_height')
		#self.setvalue_from_xml(config_expert, 'fan_speed')
		self.setvalue_from_xml(config_expert, 'fan_speed_max')
		self.setvalue_from_xml(config_expert, 'cool_min_feedrate')
		self.setvalue_from_xml(config_expert, 'cool_head_lift')
		# Infill
		self.setvalue_from_xml(config_expert, 'solid_top')
		self.setvalue_from_xml(config_expert, 'solid_bottom')
		self.setvalue_from_xml(config_expert, 'fill_overlap')
		# Support
		self.setvalue_from_xml(config_expert, 'support_type')
		self.setvalue_from_xml(config_expert, 'support_angle')
		self.setvalue_from_xml(config_expert, 'support_fill_rate')
		self.setvalue_from_xml(config_expert, 'support_xy_distance')
		self.setvalue_from_xml(config_expert, 'support_z_distance')
		# Block Magic
		self.setvalue_from_xml(config_expert, 'spiralize')
		self.setvalue_from_xml(config_expert, 'simple_mode')
		# Brim
		self.setvalue_from_xml(config_expert, 'brim_line_count')
		# Raft
		self.setvalue_from_xml(config_expert, 'raft_margin')
		self.setvalue_from_xml(config_expert, 'raft_line_spacing')
		self.setvalue_from_xml(config_expert, 'raft_base_thickness')
		self.setvalue_from_xml(config_expert, 'raft_base_linewidth')
		self.setvalue_from_xml(config_expert, 'raft_interface_thickness')
		self.setvalue_from_xml(config_expert, 'raft_interface_linewidth')
		self.setvalue_from_xml(config_expert, 'raft_airgap')
		self.setvalue_from_xml(config_expert, 'raft_surface_layers')
		# Fix Horrible
		self.setvalue_from_xml(config_expert, 'fix_horrible_union_all_type_a')
		self.setvalue_from_xml(config_expert, 'fix_horrible_union_all_type_b')
		self.setvalue_from_xml(config_expert, 'fix_horrible_use_open_bits')
		self.setvalue_from_xml(config_expert, 'fix_horrible_extensive_stitching')

	def init_Config_Preferences(self):
		config_pref = doc.getElementsByTagName("Config_Preferences")[0]
		# Colours
		self.setvalue_from_xml_pref(config_pref, 'model_colour')
		# Filament Settings
		#self.setvalue_from_xml_pref(config_pref, 'filament_physical_density')
		#self.setvalue_from_xml_pref(config_pref, 'filament_cost_kg')
		#Cura Settings
		self.setvalue_from_xml_pref(config_pref, 'auto_detect_sd')
		self.setvalue_from_xml_pref(config_pref, 'check_for_updates')
		self.setvalue_from_xml_pref(config_pref, 'submit_slice_information')


	def get_filaments(self):
		filaments = doc.getElementsByTagName("Filament")
		self.filaments = []
		choices = []
		for filament in filaments:
			if filament.hasAttributes():
				fila = self.Filament()
				name = filament.getAttribute("name")
				choices.append(_(name))
				fila.type = name
			try :
				if len(filament.getElementsByTagName("grip_temperature")) > 0:
					fila.grip_temperature = self.getNodeText(filament.getElementsByTagName("grip_temperature")[0])
				else:
					fila.grip_temperature = self.getNodeText(filament.getElementsByTagName("print_temperature")[0])
				fila.print_temperature = self.getNodeText(filament.getElementsByTagName("print_temperature")[0])
				fila.filament_diameter = self.getNodeText(filament.getElementsByTagName("filament_diameter")[0])
				fila.filament_flow = self.getNodeText(filament.getElementsByTagName("filament_flow")[0])
				fila.retraction_speed = self.getNodeText(filament.getElementsByTagName("retraction_speed")[0])
				fila.retraction_amount = self.getNodeText(filament.getElementsByTagName("retraction_amount")[0])
				fila.filament_physical_density = self.getNodeText(filament.getElementsByTagName("filament_physical_density")[0])
				fila.filament_cost_kg = self.getNodeText(filament.getElementsByTagName("filament_cost_kg")[0])
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
		remplissages = doc.getElementsByTagName("Filling")
		if len(remplissages) == 0:
			remplissages = doc.getElementsByTagName("Remplissage")
		choices = []
		self.remplissages = []
		for remplissage in remplissages:
			if remplissage.hasAttributes():
				rempli = self.Remplissage()
				name = _(remplissage.getAttribute("name"))
				choices.append(name)
				rempli.type = name
				try :
					rempli.fill_density = self.getNodeText(remplissage.getElementsByTagName("fill_density")[0])
					self.remplissages.append(rempli)
				except:
					print 'Some Errors in Remplissage Bloc'
					pass
		self.radio_box_2 = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices = choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.radio_box_2.SetSelection(int(profile.getPreference('fill_index')))

	def get_Precision(self):
		bloc_name = _("Quality (layer thickness) :")
		precisions = doc.getElementsByTagName("Precision")
		choices = []
		self.precisions = []
		for precision in precisions:
			if precision.hasAttributes():
				preci = self.Precision()
				name = precision.getAttribute("name")
				choices.append(_(name))
				preci.type = name
				try :
					preci.layer_height = self.getNodeText(precision.getElementsByTagName("layer_height")[0])
					preci.solid_layer_thickness = self.getNodeText(precision.getElementsByTagName("solid_layer_thickness")[0])
					preci.wall_thickness = self.getNodeText(precision.getElementsByTagName("wall_thickness")[0])
					preci.print_speed = self.getNodeText(precision.getElementsByTagName("print_speed")[0])
					preci.temp_preci = self.getNodeText(precision.getElementsByTagName("temp_preci")[0])
					preci.travel_speed = self.getNodeText(precision.getElementsByTagName("travel_speed")[0])
					preci.bottom_layer_speed = self.getNodeText(precision.getElementsByTagName("bottom_layer_speed")[0])
					preci.infill_speed = self.getNodeText(precision.getElementsByTagName("infill_speed")[0])
					preci.inset0_speed = self.getNodeText(precision.getElementsByTagName("inset0_speed")[0])
					preci.insetx_speed = self.getNodeText(precision.getElementsByTagName("insetx_speed")[0])
					self.precisions.append(preci)
				except :
					print 'Some Error in Precision Bloc'
					pass
		self.radio_box_1 = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.radio_box_1.SetSelection(int(profile.getPreference('precision_index')))

	def get_Tete(self):
		bloc_name = _("Printhead version :")
		tetes = doc.getElementsByTagName("PrinterHead")
		if len(tetes) == 0:
			tetes = doc.getElementsByTagName("Tete")
		choices = []
		self.tetes = []
		for tete in tetes:
			if tete.hasAttributes():
				tet = self.Tete()
				name = tete.getAttribute("name")
				choices.append(_(name))
				tet.type = name
				try :
					tet.fan_speed = self.getNodeText(tete.getElementsByTagName("fan_speed")[0])
					tet.cool_min_layer_time = self.getNodeText(tete.getElementsByTagName("cool_min_layer_time")[0])
					self.tetes.append(tet)
				except :
					print 'Some Error in Tete Bloc'
					pass
		self.tetes_box = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
		self.tetes_box.SetSelection(int(profile.getPreference('printhead_index')))

	def get_support(self):
		bloc_name = _("Printing supports :")
		supports = doc.getElementsByTagName("Support")
		choices = []
		self.supports = []
		for support in supports:
			if support.hasAttributes():
				supp = self.Support()
				name = _(support.getAttribute("name"))
				choices.append(name)
				supp.type = name
				try :
					supp.support = self.getNodeText(support.getElementsByTagName("support")[0])
					self.supports.append(supp)
				except :
					print 'Some Error in Supports Bloc'
					pass
		self.printsupp = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

	def get_brim(self):
		bloc_name = _("Improve the adhesion surface")
		self.printbrim = wx.CheckBox(self, wx.ID_ANY, bloc_name)
		brim_enable = doc.getElementsByTagName("Brim_Enable")
		brim_disable = doc.getElementsByTagName("Brim_Disable")
		self.brims = []
		self.brims.append(self.Brim())
		self.brims[0].platform_adhesion = self.getNodeText(brim_enable[0].getElementsByTagName("platform_adhesion")[0])
		self.brims.append(self.Brim())
		self.brims[1].platform_adhesion = self.getNodeText(brim_disable[0].getElementsByTagName("platform_adhesion")[0])

	# Fonction qui recupere dans le xml les differentes lignes pour le bloc Palpeur
	def get_palpeur(self):
		bloc_name = _("Use the sensor")
		self.palpeur_chbx = wx.CheckBox(self, wx.ID_ANY, bloc_name)
		palpeur_enable = doc.getElementsByTagName("Sensor_Enable")
		if len(palpeur_enable) == 0:
			palpeur_enable = doc.getElementsByTagName("Palpeur_Enable")
			sensor_enabled = palpeur_enable[0].getElementsByTagName("palpeur")[0]
		else:
			sensor_enabled = palpeur_enable[0].getElementsByTagName("value")[0]
		palpeur_disable = doc.getElementsByTagName("Sensor_Disable")
		if len(palpeur_disable) == 0:
			palpeur_disable = doc.getElementsByTagName("Palpeur_Disable")
			sensor_disabled = palpeur_disable[0].getElementsByTagName("palpeur")[0]
		else:
			sensor_disabled = palpeur_disable[0].getElementsByTagName("value")[0]
		self.palpeurs = []
		self.palpeurs.append(self.Palpeur())
		self.palpeurs[0].palpeur = self.getNodeText(sensor_enabled)
		self.palpeurs.append(self.Palpeur())
		self.palpeurs[1].palpeur = self.getNodeText(sensor_disabled)

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
		filaments = doc.getElementsByTagName("Filament")
		colors = filaments[filament_index].getElementsByTagName("Color")
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
			filaments = doc.getElementsByTagName("Filament")
			colors = filaments[filament_index].getElementsByTagName("Color")
			color = colors[color_index]
			try:
				grip_temperature = self.getNodeText(color.getElementsByTagName("grip_temperature")[0])
				profile.putProfileSetting('grip_temperature', grip_temperature)
			except:
				pass

			try:
				print_temperature = self.getNodeText(color.getElementsByTagName("print_temperature")[0])
				calculated_print_temperature = float(print_temperature)
				if not self.spin_ctrl_1.IsEnabled():
					calculated_print_temperature += self.temp_preci
				self.spin_ctrl_1.SetValue(calculated_print_temperature)
				profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
			except:
				pass

			try:
				filament_diameter = self.getNodeText(color.getElementsByTagName("filament_diameter")[0])
				profile.putProfileSetting('filament_diameter', filament_diameter)
			except:
				pass

			try:
				filament_flow = self.getNodeText(color.getElementsByTagName("filament_flow")[0])
				profile.putProfileSetting('filament_flow', filament_flow)
			except:
				pass

			try:
				retraction_speed = self.getNodeText(color.getElementsByTagName("retraction_speed")[0])
				profile.putProfileSetting('retraction_speed', retraction_speed)
			except:
				pass

			try:
				retraction_amount = self.getNodeText(color.getElementsByTagName("retraction_amount")[0])
				profile.putProfileSetting('retraction_amount', retraction_amount)
			except:
				pass

			try:
				filament_physical_density = self.getNodeText(color.getElementsByTagName("filament_physical_density")[0])
				profile.putProfileSetting('filament_physical_density', filament_physical_density)
			except:
				pass

			try:
				filament_cost_kg = self.getNodeText(color.getElementsByTagName("filament_cost_kg")[0])
				profile.putProfileSetting('filament_cost_kg', filament_cost_kg)
			except:
				pass
		else:
			fila = self.filaments[filament_index]
			profile.putProfileSetting('grip_temperature', fila.grip_temperature)
			calculated_print_temperature = float(fila.print_temperature)
			if not self.spin_ctrl_1.IsEnabled():
				calculated_print_temperature += self.temp_preci
			self.spin_ctrl_1.SetValue(calculated_print_temperature)
			profile.putProfileSetting('print_temperature', str(calculated_print_temperature))
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

 	def Print_All(self):
		print '********* Slicing parameters *********'
		print "print_temperature : ", profile.getProfileSetting('print_temperature')
		print "nozzle_size : ", profile.getProfileSetting('nozzle_size')
		print "rectration_enable : ", profile.getProfileSetting('retraction_enable')
		print "fan_full_height : ", profile.getProfileSetting('fan_full_height')
		print "fan_speed : ", profile.getProfileSetting('fan_speed')
		print "fan_speed_max : ", profile.getProfileSetting('fan_speed_max')
		print "coll_min_feedrate : ", profile.getProfileSetting('cool_min_feedrate')
		print "filament_diameter : ", profile.getProfileSetting('filament_diameter')
		print "filament_flow : ", profile.getProfileSetting('filament_flow')
		print "retraction_speed : ", profile.getProfileSetting('retraction_speed')
		print "retraction_amount : ", profile.getProfileSetting('retraction_amount')
		print "filament_physical_density : ", profile.getProfileSetting('filament_physical_density')
		print "filament_cost_kg : ", profile.getProfileSetting('filament_cost_kg')
		print "fill_density", profile.getProfileSetting('fill_density')
		print "layer_height ", profile.getProfileSetting('layer_height')
		print "solid_layer_thickness : ", profile.getProfileSetting('solid_layer_thickness')
		print "wall_thickness : ", profile.getProfileSetting('wall_thickness')
		print "print_speed : ", profile.getProfileSetting('print_speed')
		print "travel_speed : ", profile.getProfileSetting('travel_speed')
		print "bottom_layer_speed : ", profile.getProfileSetting('bottom_layer_speed')
		print "infill_speed : ", profile.getProfileSetting('infill_speed')
		print "inset0_speed : ", profile.getProfileSetting('inset0_speed')
		print "insetx_speed : ", profile.getProfileSetting('insetx_speed')
		print "fan_speed ", profile.getProfileSetting('fan_speed')
		print "cool_min_layer_time : ", profile.getProfileSetting('cool_min_layer_time')
		print "support : ", profile.getProfileSetting('support')
		print "platform_adhesion : ", profile.getProfileSetting('platform_adhesion')
		print "palpeur_enable : ", profile.getProfileSetting('palpeur_enable')
		print '**************************************'


	def Click_Button(self, event):
		profile.putProfileSetting('print_temperature', str(self.spin_ctrl_1.GetValue()))
		self.Print_All()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
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
