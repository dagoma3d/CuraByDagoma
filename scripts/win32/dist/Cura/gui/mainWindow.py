#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import os
import webbrowser
import sys


from Cura.gui import configBase
from Cura.gui import expertConfig
from Cura.gui import alterationPanel
from Cura.gui import pluginPanel
from Cura.gui import preferencesDialog
from Cura.gui import configWizard
from Cura.gui import firmwareInstall
from Cura.gui import simpleMode
from Cura.gui import sceneView
from Cura.gui import aboutWindow
from Cura.gui.util import dropTarget
#from Cura.gui.tools import batchRun
from Cura.gui.tools import pidDebugger
from Cura.gui.tools import minecraftImport
from Cura.util import profile
from Cura.util import version
import platform
from Cura.util import meshLoader

from Cura.util import resources
from xml.dom import minidom

doc = minidom.parse(resources.getPathForXML('xml_config.xml'))

#
# MAINTENANT
#
class mainWindow(wx.Frame):
	def __init__(self):
		super(mainWindow, self).__init__(None, title='Cura by dagoma Easy200 V1.0.2')#+doc.getElementsByTagName("Version")[0])# version.getVersion()
    	
		wx.EVT_CLOSE(self, self.OnClose)

		# allow dropping any file, restrict later
		
		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles))
		
		# frameicone = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO) #MOI Ajoute Icone dagoma.ico
		# self.SetIcon(frameicone)

		# TODO: wxWidgets 2.9.4 has a bug when NSView does not register for dragged types when wx drop target is set. It was fixed in 2.9.5
		if sys.platform.startswith('darwin'):
			try:
				import objc
				nswindow = objc.objc_object(c_void_p=self.MacGetTopLevelWindowRef())
				view = nswindow.contentView()
				view.registerForDraggedTypes_([u'NSFilenamesPboardType'])
			except:
				pass

		self.normalModeOnlyItems = []

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(appName="Cura by Dagoma Easy200",
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

		# self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, _("Ouvrir un Objet\tCTRL+L".decode('utf-8')))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showLoadModel(), i)
		# i = self.fileMenu.Append(-1, _("Save model...\tCTRL+S"))
		# self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveModel(), i)
		# i = self.fileMenu.Append(-1, _("Reload platform\tF5"))
		# # self.Bind(wx.EVT_MENU, lambda e: self.scene.reloadScene(e), i)
		# i = self.fileMenu.Append(-1, _("Clear platform"))
		# self.Bind(wx.EVT_MENU, lambda e: self.scene.OnDeleteAll(e), i)

		# self.fileMenu.AppendSeparator()
		# i = self.fileMenu.Append(-1, _("Print...\tCTRL+P"))
		# # self.Bind(wx.EVT_MENU, lambda e: self.scene.OnPrintButton(1), i)
		i = self.fileMenu.Append(1, 'Préparer l\'Impression\tCTRL+S'.decode('utf-8'))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveGCode(), i)
		# i = self.fileMenu.Append(-1, _("Show slice engine log..."))
		# self.Bind(wx.EVT_MENU, lambda e: self.scene._showEngineLog(), i)
		# self.fileMenu.AppendSeparator()
		
		# i = self.fileMenu.Append(-1, _("Open Profile..."))
		# self.normalModeOnlyItems.append(i)
		# self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		
		# i = self.fileMenu.Append(-1, _("Save Profile..."))
		# self.normalModeOnlyItems.append(i)
		# self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		
		# i = self.fileMenu.Append(-1, _("Load Profile from GCode..."))
		# self.normalModeOnlyItems.append(i)
		# self.Bind(wx.EVT_MENU, self.OnLoadProfileFromGcode, i)
		# self.fileMenu.AppendSeparator()
		
		# i = self.fileMenu.Append(-1, _("Reset Profile to default"))
		# self.normalModeOnlyItems.append(i)
		# self.Bind(wx.EVT_MENU, self.OnResetProfile, i)

		# self.fileMenu.AppendSeparator()
		
		# i = self.fileMenu.Append(-1, _("Preferences...\tCTRL+P"))
		# self.Bind(wx.EVT_MENU, self.OnPreferences, i)
		 
		# i = self.fileMenu.Append(-1, _("Machine settings...\tCTRL+M"))
		# self.Bind(wx.EVT_MENU, self.OnMachineSettings, i)
		 
		# i = self.fileMenu.Append(-1, _("Expert settings...\tCTRL+E"))
		# self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		
		# self.fileMenu.AppendSeparator()
		
		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), '&' + _("Objets Récemment Ouverts".decode('utf-8')), modelHistoryMenu)
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		# Profle MRU list
		# profileHistoryMenu = wx.Menu()
		# self.fileMenu.AppendMenu(wx.NewId(), _("Recent Profile Files"), profileHistoryMenu)
		# self.profileFileHistory.UseMenu(profileHistoryMenu)
		# self.profileFileHistory.AddFilesToMenu()
		# self.Bind(wx.EVT_MENU_RANGE, self.OnProfileMRU, id=self.ID_MRU_PROFILE1, id2=self.ID_MRU_PROFILE10)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, _("Quitter"))
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		# self.menubar.Append(self.fileMenu, '&' + _("File"))

		toolsMenu = wx.Menu()
		#i = toolsMenu.Append(-1, 'Batch run...')
		#self.Bind(wx.EVT_MENU, self.OnBatchRun, i)
		#self.normalModeOnlyItems.append(i)


		# Dagoma Menu //Hiden on Linux
		menuBar = wx.MenuBar()
		menuBar.Append(self.fileMenu, 'Fichier')
		self.SetMenuBar(menuBar)
		menuBar.Hide()
		menuBar.Show(False)

		if minecraftImport.hasMinecraft():
			i = toolsMenu.Append(-1, _("Minecraft map import..."))
			self.Bind(wx.EVT_MENU, self.OnMinecraftImport, i)

		if version.isDevVersion():
			i = toolsMenu.Append(-1, _("PID Debugger..."))
			self.Bind(wx.EVT_MENU, self.OnPIDDebugger, i)

		i = toolsMenu.Append(-1, _("Copy profile to clipboard"))
		self.Bind(wx.EVT_MENU, self.onCopyProfileClipboard,i)

		toolsMenu.AppendSeparator()
		self.allAtOnceItem = toolsMenu.Append(-1, _("Print all at once"), kind=wx.ITEM_RADIO)
		self.Bind(wx.EVT_MENU, self.onOneAtATimeSwitch, self.allAtOnceItem)
		self.oneAtATime = toolsMenu.Append(-1, _("Print one at a time"), kind=wx.ITEM_RADIO)
		self.Bind(wx.EVT_MENU, self.onOneAtATimeSwitch, self.oneAtATime)
		if profile.getPreference('oneAtATime') == 'True':
			self.oneAtATime.Check(True)
		else:
			self.allAtOnceItem.Check(True)


		# self.menubar.Append(toolsMenu, _("Tools"))

		#Machine menu for machine configuration/tooling
		self.machineMenu = wx.Menu()
		self.updateMachineMenu()

		# self.menubar.Append(self.machineMenu, _("Machine"))

		expertMenu = wx.Menu()
		i = expertMenu.Append(-1, _("Switch to quickprint..."), kind=wx.ITEM_RADIO)
		self.switchToQuickprintMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnSimpleSwitch, i)

		i = expertMenu.Append(-1, _("Switch to full settings..."), kind=wx.ITEM_RADIO)
		self.switchToNormalMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnNormalSwitch, i)
		expertMenu.AppendSeparator()

		i = expertMenu.Append(-1, _("Open expert settings...\tCTRL+E"))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		expertMenu.AppendSeparator()

		i = expertMenu.Append(-1, _("Run first run wizard..."))
		self.Bind(wx.EVT_MENU, self.OnFirstRunWizard, i)
		self.bedLevelWizardMenuItem = expertMenu.Append(-1, _("Run bed leveling wizard..."))
		self.Bind(wx.EVT_MENU, self.OnBedLevelWizard, self.bedLevelWizardMenuItem)
		self.headOffsetWizardMenuItem = expertMenu.Append(-1, _("Run head offset wizard..."))
		self.Bind(wx.EVT_MENU, self.OnHeadOffsetWizard, self.headOffsetWizardMenuItem)

		# self.menubar.Append(expertMenu, _("Expert"))


		helpMenu = wx.Menu()
		# i = helpMenu.Append(-1, _("Online documentation..."))
		# self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('http://daid.github.com/Cura'), i)
		 
		# i = helpMenu.Append(-1, _("Report a problem..."))
		# self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://github.com/daid/Cura/issues'), i)
		 
		# i = helpMenu.Append(-1, _("Check for update..."))
		# self.Bind(wx.EVT_MENU, self.OnCheckForUpdate, i)
		 
		# i = helpMenu.Append(-1, _("Open YouMagine website..."))
		# self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://www.youmagine.com/'), i)
		 
		# i = helpMenu.Append(-1, _("About Cura..."))
		# self.Bind(wx.EVT_MENU, self.OnAbout, i)
		
		# self.menubar.Append(helpMenu, _("Help"))
		# self.SetMenuBar(self.menubar)
		# self.menubar.Hide() # Dagoma

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3D | wx.SP_LIVE_UPDATE)
		self.rightPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.leftPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		# self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		##Gui components##
		self.simpleSettingsPanel = simpleMode.simpleModePanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated())

		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.Add(self.simpleSettingsPanel, 1, wx.EXPAND) #Dagoma Add wx.EXPAND
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.leftPane.SetSizer(self.leftSizer)

		#Preview window
		self.scene = sceneView.SceneView(self.rightPane)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.rightPane.SetSizer(sizer)
		sizer.Add(self.scene, 1, flag=wx.EXPAND)

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		sizer.Layout()
		self.sizer = sizer

		self.updateProfileToAllControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		self.simpleSettingsPanel.Show(False)
		self.normalSettingsPanel.Show(False)

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2,wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()

		#Timer set; used to check if profile is on the clipboard
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer)
		self.timer.Start(1000)
		self.lastTriedClipboard = profile.getProfileString()

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

			self.normalSashPos = int(profile.getPreference('window_normal_sash'))
		except:
			self.normalSashPos = 0
			self.Maximize(True)

		self.SetMinSize((940,600))
		self.leftPane.SetMinSize((250, 600))
		self.rightPane.SetMinSize((640,600))
		# self.splitter.SplitVertically(self.leftPane, self.rightPane, self.normalSashPos)
		self.splitter.SplitVertically(self.rightPane, self.leftPane, self.normalSashPos) #Left and Right are switched in code
		self.splitter.SetSashGravity(1.0) # Only the SceneView are resize when the windows size are modifed
		# self.splitter.SetMinimumPaneSize(470)

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800,600))
			self.Centre()

		self.Bind(wx.EVT_SIZE, self.mainResize)
		self.updateSliceMode()
		self.scene.SetFocus()


	def mainResize(self, e):
		x, y = self.GetSize()
		self.rightPane.SetMinSize((x/2,520))
		e.Skip()

	def onTimer(self, e):
		#Check if there is something in the clipboard
		profileString = ""
		try:
			if not wx.TheClipboard.IsOpened():
				if not wx.TheClipboard.Open():
					return
				do = wx.TextDataObject()
				if wx.TheClipboard.GetData(do):
					profileString = do.GetText()
				wx.TheClipboard.Close()

				startTag = "CURA_PROFILE_STRING:"
				if startTag in profileString:
					#print "Found correct syntax on clipboard"
					profileString = profileString.replace("\n","").strip()
					profileString = profileString[profileString.find(startTag)+len(startTag):]
					if profileString != self.lastTriedClipboard:
						print profileString
						self.lastTriedClipboard = profileString
						profile.setProfileFromString(profileString)
						self.scene.notification.message("Loaded new profile from clipboard.")
						self.updateProfileToAllControls()
		except:
			print "Unable to read from clipboard"


	def updateSliceMode(self):
		isSimple = profile.getPreference('startMode') == 'Simple'

		self.normalSettingsPanel.Show(not isSimple)
		self.simpleSettingsPanel.Show(isSimple)
		self.leftPane.Layout()

		for i in self.normalModeOnlyItems:
			i.Enable(not isSimple)
		if isSimple:
			self.switchToQuickprintMenuItem.Check()
		else:
			self.switchToNormalMenuItem.Check()

			# MOI Enabled splitter for all setting panel
		# Set splitter sash position & size
#		if isSimple:
			# Save normal mode sash
#			self.normalSashPos = self.splitter.GetSashPosition()

			# Change location of sash to width of quick mode pane
#			(width, height) = self.simpleSettingsPanel.GetSizer().GetSize()
#			self.splitter.SetSashPosition(width, True)

			# Disable sash
#			self.splitter.SetSashSize(4)
#		else:
		self.splitter.SetSashPosition(self.normalSashPos, True)
			# Enabled sash
		self.splitter.SetSashSize(4)
		self.defaultFirmwareInstallMenuItem.Enable(firmwareInstall.getDefaultFirmware() is not None)
		if profile.getMachineSetting('machine_type') == 'ultimaker2':
			self.bedLevelWizardMenuItem.Enable(False)
			self.headOffsetWizardMenuItem.Enable(False)
		if int(profile.getMachineSetting('extruder_amount')) < 2:
			self.headOffsetWizardMenuItem.Enable(False)
		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()

	def onOneAtATimeSwitch(self, e):
		profile.putPreference('oneAtATime', self.oneAtATime.IsChecked())
		if self.oneAtATime.IsChecked() and profile.getMachineSettingFloat('extruder_head_size_height') < 1:
			wx.MessageBox(_('For "One at a time" printing, you need to have entered the correct head size and gantry height in the machine settings'), _('One at a time warning'), wx.OK | wx.ICON_WARNING)
		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()
		self.scene.sceneUpdated()

	def OnPreferences(self, e):
		prefDialog = preferencesDialog.preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()
		wx.CallAfter(prefDialog.Show)

	def OnMachineSettings(self, e):
		prefDialog = preferencesDialog.machineSettingsDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()

	def OnDropFiles(self, files):
		if len(files) > 0:
			self.updateProfileToAllControls()
		self.scene.loadFiles(files)

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

	def addToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()

	def updateProfileToAllControls(self):
		self.scene.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()
		self.simpleSettingsPanel.updateProfileToControls()

	def reloadSettingPanels(self):
		self.leftSizer.Detach(self.simpleSettingsPanel)
		self.leftSizer.Detach(self.normalSettingsPanel)
		self.simpleSettingsPanel.Destroy()
		self.normalSettingsPanel.Destroy()
		self.simpleSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated()) #simpleMode.simpleModePanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.leftSizer.Add(self.simpleSettingsPanel, 1)
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.updateSliceMode()
		self.updateProfileToAllControls()

	def updateMachineMenu(self):
		#Remove all items so we can rebuild the menu. Inserting items seems to cause crashes, so this is the safest way.
		for item in self.machineMenu.GetMenuItems():
			self.machineMenu.RemoveItem(item)

		#Add a menu item for each machine configuration.
		for n in xrange(0, profile.getMachineCount()):
			i = self.machineMenu.Append(n + 0x1000, profile.getMachineSetting('machine_name', n).title(), kind=wx.ITEM_RADIO)
			if n == int(profile.getPreferenceFloat('active_machine')):
				i.Check(True)
			self.Bind(wx.EVT_MENU, lambda e: self.OnSelectMachine(e.GetId() - 0x1000), i)

		self.machineMenu.AppendSeparator()

		i = self.machineMenu.Append(-1, _("Machine settings..."))
		self.Bind(wx.EVT_MENU, self.OnMachineSettings, i)

		#Add tools for machines.
		self.machineMenu.AppendSeparator()

		self.defaultFirmwareInstallMenuItem = self.machineMenu.Append(-1, _("Install default firmware..."))
		self.Bind(wx.EVT_MENU, self.OnDefaultMarlinFirmware, self.defaultFirmwareInstallMenuItem)

		i = self.machineMenu.Append(-1, _("Install custom firmware..."))
		self.Bind(wx.EVT_MENU, self.OnCustomFirmware, i)

	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, _("Select profile file to load"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.loadProfile(profileFile)
			self.updateProfileToAllControls()

			# Update the Profile MRU
			self.addToProfileMRU(profileFile)

		dlg.Destroy()
		



	def OnLoadProfileFromGcode(self, e):
		dlg=wx.FileDialog(self, _("Select gcode file to load profile from"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("gcode files (*%s)|*%s;*%s" % (profile.getGCodeExtension(), profile.getGCodeExtension(), profile.getGCodeExtension()[0:2]))
		if dlg.ShowModal() == wx.ID_OK:
			gcodeFile = dlg.GetPath()
			f = open(gcodeFile, 'r')
			hasProfile = False
			for line in f:
				if line.startswith(';CURA_PROFILE_STRING:'):
					profile.setProfileFromString(line[line.find(':')+1:].strip())
					if ';{profile_string}' not in profile.getAlterationFile('end.gcode'):
						profile.setAlterationFile('end.gcode', profile.getAlterationFile('end.gcode') + '\n;{profile_string}')
					hasProfile = True
			if hasProfile:
				self.updateProfileToAllControls()
			else:
				wx.MessageBox(_("No profile found in GCode file.\nThis feature only works with GCode files made by Cura 12.07 or newer."), _("Profile load error"), wx.OK | wx.ICON_INFORMATION)
		dlg.Destroy()

	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, _("Select profile file to save"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			if not profileFile.lower().endswith('.ini'): #hack for linux, as for some reason the .ini is not appended.
				profileFile += '.ini'
			profile.saveProfile(profileFile)
		dlg.Destroy()

	def OnResetProfile(self, e):
		dlg = wx.MessageDialog(self, _("This will reset all profile settings to defaults.\nUnless you have saved your current profile, all settings will be lost!\nDo you really want to reset?"), _("Profile reset"), wx.YES_NO | wx.ICON_QUESTION)
		result = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if result:
			profile.resetProfile()
			self.updateProfileToAllControls()

	def OnSimpleSwitch(self, e):
		profile.putPreference('startMode', 'Simple')
		self.updateSliceMode()

	def OnNormalSwitch(self, e):
		profile.putPreference('startMode', 'Normal')
		self.updateSliceMode()

	def OnDefaultMarlinFirmware(self, e):
		firmwareInstall.InstallFirmware()

	def OnCustomFirmware(self, e):
		if profile.getMachineSetting('machine_type').startswith('ultimaker'):
			wx.MessageBox(_("Warning: Installing a custom firmware does not guarantee that you machine will function correctly, and could damage your machine."), _("Firmware update"), wx.OK | wx.ICON_EXCLAMATION)
		dlg=wx.FileDialog(self, _("Open firmware to upload"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("HEX file (*.hex)|*.hex;*.HEX")
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			dlg.Destroy()
			if not(os.path.exists(filename)):
				return
			#For some reason my Ubuntu 10.10 crashes here.
			firmwareInstall.InstallFirmware(filename)

	def OnFirstRunWizard(self, e):
		self.Hide()
		configWizard.configWizard()
		self.Show()
		self.reloadSettingPanels()

	def OnSelectMachine(self, index):
		profile.setActiveMachine(index)
		self.reloadSettingPanels()

	def OnBedLevelWizard(self, e):
		configWizard.bedLevelWizard()

	def OnHeadOffsetWizard(self, e):
		configWizard.headOffsetWizard()

	def OnExpertOpen(self, e):
		ecw = expertConfig.expertConfigWindow(lambda : self.scene.sceneUpdated())
		ecw.Centre()
		ecw.Show()

	def OnMinecraftImport(self, e):
		mi = minecraftImport.minecraftImportWindow(self)
		mi.Centre()
		mi.Show(True)

	def OnPIDDebugger(self, e):
		debugger = pidDebugger.debuggerWindow(self)
		debugger.Centre()
		debugger.Show(True)

	def onCopyProfileClipboard(self, e):
		try:
			if not wx.TheClipboard.IsOpened():
				wx.TheClipboard.Open()
				clipData = wx.TextDataObject()
				self.lastTriedClipboard = profile.getProfileString()
				profileString = profile.insertNewlines("CURA_PROFILE_STRING:" + self.lastTriedClipboard)
				clipData.SetText(profileString)
				wx.TheClipboard.SetData(clipData)
				wx.TheClipboard.Close()
		except:
			print "Could not write to clipboard, unable to get ownership. Another program is using the clipboard."

	def OnCheckForUpdate(self, e):
		newVersion = version.checkForNewerVersion()
		if newVersion is not None:
			if wx.MessageBox(_("A new version of Cura is available, would you like to download?"), _("New version available"), wx.YES_NO | wx.ICON_INFORMATION) == wx.YES:
				webbrowser.open(newVersion)
		else:
			wx.MessageBox(_("You are running the latest version of Cura!"), _("Awesome!"), wx.ICON_INFORMATION)

	def OnAbout(self, e):
		# aboutBox = aboutWindow.aboutWindow() # MOI ENLEVE LA WINDOWS ABOUT 
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

			# Save normal sash position.  If in normal mode (!simple mode), get last position of sash before saving it...
			isSimple = profile.getPreference('startMode') == 'Simple'
			if not isSimple:
				self.normalSashPos = self.splitter.GetSashPosition()
			profile.putPreference('window_normal_sash', self.normalSashPos)

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
			self.print_temperature = '185'
			self.filament_diameter = '1.74'
			self.filament_flow = '80'
			
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

                
	class Support:
		def __init__(self):
			self.support = None

	class Brim:
		def __init__(self):
			self.platform_adhesion = None




	"""ERIC"""
	#Ajout class printing_surface afin de stocker les infos relative au different surface d'impression
	#
	#
	class PrintingSurface:
		def __init__(self):
			self.name = ''
			self.height = ''

	#Ajout class Offset afin de stocker les infos relative à l'offset en Z pour Dagoma
	#
	#
	class Offset:
		def __init__(self):
			self.value = ''
			self.input = ''

	#Ajout class Palpeur afin de stocker les infos relative à la présence d'un palpeur pour Dagoma
	#
	#
	class Palpeur:
		def __init__(self):
			self.palpeur = None


	"""FIN ERIC"""





	def __init__(self, parent, callback = None):
		super(normalSettingsPanel, self).__init__(parent, callback)

		self.parent = parent
		self.loadxml()
		self.label_1 = wx.StaticText(self, wx.ID_ANY, _("Filament :"))
		
		"""ERIC"""
		#Rajout d'un label pour le titre "Offset"
		#self.offset_label = wx.StaticText(self, wx.ID_ANY, _(self.offset_title))
		#Rajout d'un champ pour recuperer un float pour l'"Offset"
		#self.offset_ctrl = wx.TextCtrl(self, -1, profile.getProfileSetting('offset_input'))
		"""FIN ERIC"""


		self.label_4 = wx.StaticText(self, wx.ID_ANY, _("Température (°C) :".decode('utf-8')))
		self.spin_ctrl_1 = wx.SpinCtrl(self, wx.ID_ANY, "190", min=175, max=235, style=wx.SP_ARROW_KEYS | wx.TE_AUTO_URL)
		self.button_1 = wx.Button(self, wx.ID_ANY, _('Préparer l\'Impression'.decode('utf-8')))
		self.__set_properties()
		self.__do_layout()

		"""ERIC"""
		# Initialisation des valeurs à partir du profile
		# 
		# 
		self.Init_Palpeur_chbx()
		#self.Init_Printing_surface()
		"""FIN ERIC"""
		

		#Refresh ALL Value
		self.Refresh_Supp()
		self.Refresh_Preci()
		self.Refresh_Fila()
		self.Refresh_Rempli()
		"""ERIC"""
		#self.Refresh_Printing_surface()
		self.Refresh_Palpeur_chbx()
		#self.Refresh_Offset()
		"""FIN ERIC"""
		#self.Refresh_Checkboxsupp()
		self.Refresh_Checkboxbrim()

		profile.saveProfile(profile.getDefaultProfilePath(), True)

		# Main tabs
		# self.nb = wx.Notebook(self)
		# self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		# self.GetSizer().Add(self.nb, 1, wx.EXPAND)

		# (left, right, self.printPanel) = self.CreateDynamicConfigTab(self.nb, 'Basic')
		# self._addSettingsToPanels('basic', left, right)
		# self.SizeLabelWidths(left, right)

		# (left, right, self.advancedPanel) = self.CreateDynamicConfigTab(self.nb, 'Advanced')
		# self._addSettingsToPanels('advanced', left, right)
		# self.SizeLabelWidths(left, right)

		# #Plugin page
		# self.pluginPanel = pluginPanel.pluginPanel(self.nb, callback)
		# self.nb.AddPage(self.pluginPanel, _("Plugins"))
		# self.nb.Hide()

		#Alteration page
		# if profile.getMachineSetting('machine_name') == 'Discovery':
		# 	self.alterationPanel = alterationPanel.alterationPanel(self, callback)
		# if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
		# 	self.alterationPanel = None
		# else:
			# self.alterationPanel = alterationPanel.alterationPanel(self.nb, callback)
			# self.nb.AddPage(self.alterationPanel, "Start/End-GCode")


		#Evt Select Filament
		if sys.platform == 'darwin':
			self.Bind(wx.EVT_CHOICE, self.EVT_Fila, self.combo_box_1)
		else:
			self.Bind(wx.EVT_COMBOBOX, self.EVT_Fila, self.combo_box_1)
			self.Bind(wx.EVT_TEXT, self.EVT_Fila, self.combo_box_1)
			self.Bind(wx.EVT_TEXT_ENTER, self.EVT_Fila, self.combo_box_1)

		#Evt Select Précision
		self.Bind(wx.EVT_RADIOBOX, self.EVT_Preci, self.radio_box_1)

		self.Bind(wx.EVT_RADIOBOX, self.EVT_Supp, self.printsupp)

		#Evt Select Remplissage
		self.Bind(wx.EVT_RADIOBOX, self.EVT_Rempl, self.radio_box_2)


		"""ERIC"""


		#Evt Select printing surface
		#self.Bind(wx.EVT_RADIOBOX, self.EVT_PrtSurf, self.radio_box_3)

		#Evt Select palpeur
		self.Bind(wx.EVT_CHECKBOX, self.EVT_Checkboxpalpeur,self.palpeur_chbx)

		# evt input Text
		#self.Bind(wx.EVT_TEXT, self.EVT_Offset, self.offset_ctrl)
		"""FIN ERIC"""

		#Evt CheckboxSupport
		self.Bind(wx.EVT_CHECKBOX, self.EVT_Supp ,self.printsupp)
		#Evt CheckboxBrim
		self.Bind(wx.EVT_CHECKBOX, self.EVT_Checkboxbrim, self.printbrim)

		#Evt Print Button
		self.Bind(wx.EVT_BUTTON, self.Click_Button, self.button_1)

 		self.Bind(wx.EVT_SIZE, self.OnSize)
		

	def __set_properties(self):
		self.combo_box_1.SetSelection(0)
		self.spin_ctrl_1.Enable(False)
		self.radio_box_2.SetSelection(1)
		self.radio_box_1.SetSelection(0)
		self.printsupp.SetSelection(0)


	def __do_layout(self):
		sizer_1 = wx.GridBagSizer(10, 2)
		sizer_1.Add(self.label_1, pos=(0, 0), flag = wx.LEFT|wx.TOP, border = 5)
		sizer_1.Add(self.combo_box_1, pos = (1, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.Add(self.label_4, pos = (2, 0), flag = wx.LEFT|wx.TOP,  border = 5)
		sizer_1.Add(self.spin_ctrl_1, pos = (3, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.Add(self.radio_box_2, pos = (4, 0) , span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.Add(self.radio_box_1, pos = (5, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		"""ERIC"""
		# Positionnementdu du bloc palpeur en position 6
		# Positionnementdu titre Offset en position 7
		#sizer_1.Add(self.offset_label, pos = (7, 0), flag = wx.LEFT|wx.TOP,  border = 5)
		# Positionnementdu de l'imput Offset en position 8
		#sizer_1.Add(self.offset_ctrl, pos = (8, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		# Positionnementdu du bloc Printing Surface en position 9
		#sizer_1.Add(self.radio_box_3, pos = (9, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		"""FIN ERIC"""
		sizer_1.Add(self.printsupp, pos = (6, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.Add(self.palpeur_chbx, pos = (7, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.Add(self.printbrim, pos = (8, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.Add(self.button_1, pos = (10, 0), span = (1, 3), flag = wx.LEFT|wx.EXPAND|wx.RIGHT, border = 5)
		sizer_1.AddGrowableCol(1)
		sizer_1.AddGrowableRow(12)
		self.SetSizerAndFit(sizer_1)

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
		self.get_support()
		self.get_brim()
		"""ERIC"""
		#self.get_Offset()
		#self.get_printing_surface()
		self.get_palpeur()
		"""FIN ERIC"""
		self.init_Config_Preferences()
		self.init_Config_Adv()
		self.init_Config_Expert()
		
	def setvalue_from_xml(self, sub, var):
		profile.putProfileSetting(var, self.getNodeText(sub.getElementsByTagName(var)[0]))

	def setvalue_from_xml_pref(self, sub, var):
		profile.putPreference(var, self.getNodeText(sub.getElementsByTagName(var)[0]))

	def init_Config_Adv(self):
		config_adv = doc.getElementsByTagName("Config_Adv")[0]
		# Retraction Adv
		self.setvalue_from_xml(config_adv, 'retraction_speed')
		self.setvalue_from_xml(config_adv, 'retraction_amount')
		# Quality
		self.setvalue_from_xml(config_adv, 'bottom_thickness')
		self.setvalue_from_xml(config_adv, 'layer0_width_factor')
		self.setvalue_from_xml(config_adv, 'object_sink')
		# # Speed
		# self.setvalue_from_xml(config_adv, 'infill_speed')
		# self.setvalue_from_xml(config_adv, 'inset0_speed')
		# self.setvalue_from_xml(config_adv, 'insetx_speed')
		# Cool
		self.setvalue_from_xml(config_adv, 'cool_min_layer_time')
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
		self.setvalue_from_xml(config_expert, 'fan_speed')
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
		self.setvalue_from_xml_pref(config_pref, 'filament_physical_density')
		self.setvalue_from_xml_pref(config_pref, 'filament_cost_kg')
		self.setvalue_from_xml_pref(config_pref, 'filament_cost_meter')
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
				name = (filament.getAttribute("name"))
				choices.append(name)
				fila.type = name
			try :
				fila.print_temperature = self.getNodeText(filament.getElementsByTagName("print_temperature")[0])
				fila.filament_diameter = self.getNodeText(filament.getElementsByTagName("filament_diameter")[0])
				fila.filament_flow = self.getNodeText(filament.getElementsByTagName("filament_flow")[0])
				self.filaments.append(fila)
			except:
				print 'Some Error in Filament Bloc'
				pass
		if sys.platform == 'darwin': #Change Combobox to an Choice cause in MAC OS X Combobox have some bug
			self.combo_box_1 = wx.Choice(self, wx.ID_ANY, choices = choices) 
		else:
			self.combo_box_1 = wx.ComboBox(self, wx.ID_ANY, choices = choices , style=wx.CB_DROPDOWN | wx.CB_SIMPLE | wx.CB_READONLY)


	def get_remplissage(self):
		bloc_name = doc.getElementsByTagName("Bloc_Remplissage")[0].getAttribute("label")
		remplissages = doc.getElementsByTagName("Remplissage")
		choices = []
		self.remplissages = []
		for remplissage in remplissages:
			if remplissage.hasAttributes():
				rempli = self.Remplissage()
				choices.append(remplissage.getAttribute("name"))
				rempli.type = remplissage.getAttribute("name")
				try : 
					rempli.fill_density = self.getNodeText(remplissage.getElementsByTagName("fill_density")[0])
					self.remplissages.append(rempli)
				except:
					print 'Some Errors in Remplissage Bloc'
					pass
		self.radio_box_2 = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices = choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

	def get_Precision(self):
		bloc_name = doc.getElementsByTagName("Bloc_Precision")[0].getAttribute("label")
		precisions = doc.getElementsByTagName("Precision")
		choices = []
		self.precisions = []
		for precision in precisions:
			if precision.hasAttributes():
				preci = self.Precision()
				choices.append(precision.getAttribute("name"))
				preci.type = precision.getAttribute("name")
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

	def get_support(self):
		bloc_name = doc.getElementsByTagName("Bloc_Support")[0].getAttribute("label")
		supports = doc.getElementsByTagName("Support")
		choices = []
		self.supports = []
		for support in supports:
			if support.hasAttributes():
				supp = self.Support()
				choices.append(support.getAttribute("name"))
				supp.type = support.getAttribute("name")
				try :
					supp.support = self.getNodeText(support.getElementsByTagName("support")[0])
					self.supports.append(supp)
				except :
					print 'Some Error in Supports Bloc'
					pass
		self.printsupp = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
	

	#def get_support(self):
	#	bloc_name = doc.getElementsByTagName("Bloc_Support")[0].getAttribute("label")
	#	self.printsupp = wx.CheckBox(self, wx.ID_ANY, bloc_name)
	#	support_enable = doc.getElementsByTagName("Support_Enable")
	#	support_disable = doc.getElementsByTagName("Support_Disable")
	#	self.supports = []
	#	self.supports.append(self.Support())
	#	self.supports[0].support = self.getNodeText(support_enable[0].getElementsByTagName("support")[0])
	#	# self.supports[0].platform_adhesion = self.getNodeText(support_enable[0].getElementsByTagName("platform_adhesion")[0])
	#	self.supports.append(self.Support())
	#	self.supports[1].support = self.getNodeText(support_disable[0].getElementsByTagName("support")[0])
	#	# self.supports[1].platform_adhesion = self.getNodeText(support_disable[0].getElementsByTagName("platform_adhesion")[0])

	def get_brim(self):
		bloc_name = doc.getElementsByTagName("Bloc_Brim")[0].getAttribute("label")
		self.printbrim = wx.CheckBox(self, wx.ID_ANY, bloc_name)
		brim_enable = doc.getElementsByTagName("Brim_Enable")
		brim_disable = doc.getElementsByTagName("Brim_Disable")
		self.brims = []
		self.brims.append(self.Brim())
		self.brims[0].platform_adhesion = self.getNodeText(brim_enable[0].getElementsByTagName("platform_adhesion")[0])
		self.brims.append(self.Brim())
		self.brims[1].platform_adhesion = self.getNodeText(brim_disable[0].getElementsByTagName("platform_adhesion")[0])


	"""ERIC"""
	#Fonction qui recupere dans le xml les differentes lignes pour le bloc Palpeur
	#
	#
	def get_palpeur(self):
		bloc_name = doc.getElementsByTagName("Bloc_Palpeur")[0].getAttribute("label")
		self.palpeur_chbx = wx.CheckBox(self, wx.ID_ANY, bloc_name)
		palpeur_enable = doc.getElementsByTagName("Palpeur_Enable")
		palpeur_disable = doc.getElementsByTagName("Palpeur_Disable")
		self.palpeurs = []
		self.palpeurs.append(self.Palpeur())
		self.palpeurs[0].palpeur = self.getNodeText(palpeur_enable[0].getElementsByTagName("palpeur")[0])
		self.palpeurs.append(self.Palpeur())
		self.palpeurs[1].palpeur = self.getNodeText(palpeur_disable[0].getElementsByTagName("palpeur")[0])

	
	#Fonction qui recupere dans le xml les differentes lignes pour le bloc Offset
	#
	#
	#def get_Offset(self):
	#	self.offset_title = doc.getElementsByTagName("Bloc_Offset")[0].getAttribute("label")


	#Fonction qui recupere dans le xml les differentes lignes pour le bloc Pritning Surface
	#
	#
	def get_printing_surface(self):
		bloc_name = doc.getElementsByTagName("Bloc_Printing_surface")[0].getAttribute("label")

		
		printing_surfaces = doc.getElementsByTagName("Printing_surface")
		choices = []
		self.printing_surfaces = []

		for printing_surface in printing_surfaces:
			if printing_surface.hasAttributes():
				prtsurf = self.PrintingSurface()
				choices.append(printing_surface.getAttribute("name"))
				prtsurf.name = printing_surface.getAttribute("name")
				try :
					prtsurf.height = self.getNodeText(printing_surface.getElementsByTagName("printing_surface_height")[0])
					self.printing_surfaces.append(prtsurf)
				except :
					print 'Some Error in Printing Surface Bloc'
					pass
		self.radio_box_3 = wx.RadioBox(self, wx.ID_ANY, bloc_name, choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
	"""FIN ERIC"""


	def Refresh_Fila(self):
		fila = self.filaments[self.combo_box_1.GetSelection()]
		if fila.type == 'Autre PLA':
			self.spin_ctrl_1.Enable(True)
		else:
			self.spin_ctrl_1.Enable(False)
		self.spin_ctrl_1.SetValue(float(fila.print_temperature))            
		profile.putProfileSetting('filament_diameter', fila.filament_diameter)
		profile.putProfileSetting('filament_flow', fila.filament_flow)
		profile.putProfileSetting('print_temperature', str(self.spin_ctrl_1.GetValue() + self.temp_preci))
				
	def Refresh_Rempli(self):
		rempli = self.remplissages[self.radio_box_2.GetSelection()]
		profile.putProfileSetting('fill_density', rempli.fill_density)

	def Refresh_Preci(self):
		preci = self.precisions[self.radio_box_1.GetSelection()]
		profile.putProfileSetting('layer_height', preci.layer_height)
		profile.putProfileSetting('solid_layer_thickness', preci.solid_layer_thickness)
		profile.putProfileSetting('wall_thickness', preci.wall_thickness)
		profile.putProfileSetting('print_speed', preci.print_speed)
		self.temp_preci = float(preci.temp_preci)
		profile.putProfileSetting('print_temperature', str(self.spin_ctrl_1.GetValue() + self.temp_preci))
		profile.putProfileSetting('travel_speed', preci.travel_speed)
		profile.putProfileSetting('bottom_layer_speed', preci.bottom_layer_speed)
		# Speed
		profile.putProfileSetting('infill_speed', preci.infill_speed)
		profile.putProfileSetting('inset0_speed', preci.inset0_speed)
		profile.putProfileSetting('insetx_speed', preci.insetx_speed)

	def Refresh_Supp(self):
		supp = self.supports[self.printsupp.GetSelection()]
		profile.putProfileSetting('support', supp.support)
		
	#def Refresh_Checkboxsupp(self):
	#	if self.printsupp.GetValue():
	#		profile.putProfileSetting('support', self.supports[0].support)
	#	else:
	#		profile.putProfileSetting('support', self.supports[1].support)

	def Refresh_Checkboxbrim(self):
		if self.printbrim.GetValue():
			profile.putProfileSetting('platform_adhesion', self.brims[0].platform_adhesion)
		else:
			profile.putProfileSetting('platform_adhesion', self.brims[1].platform_adhesion)


	"""ERIC"""

	#fonction pour initialiser la checkbox palpeur dans le profil
	#
	#
	def Init_Palpeur_chbx(self):
		#if profile.getProfileSetting('palpeur_enable') == 'Palpeur':
		#	self.palpeur_chbx.SetValue(True)

		#else :
		#	self.palpeur_chbx.SetValue(False)
		self.palpeur_chbx.SetValue(True)	
		self.palpeur_chbx.Refresh()


	#fonction pour initialiser la checkbox palpeur dans le profil
	#
	#
	def Init_Printing_surface(self):
		self.radio_box_3.SetStringSelection(profile.getProfileSetting('printing_surface_name'))
		self.radio_box_3.Refresh()


	#fonction qui verif si un str est un floatant
	#
	#
	def is_number(self, zeString):
		try:
			float(zeString)
			return True
		except ValueError:
			return False


	#fonction pour calcul l'offset en fonction 
	#
	#
	def calculateZOffset(self):
		printing_surface_height = float(profile.getProfileSetting('printing_surface_height')) 
		offset_input = float(profile.getProfileSetting('offset_input')) 
		offset_value = offset_input - printing_surface_height
		profile.putProfileSetting('offset_value', offset_value)
		

	#fonction pour enregistrer les données relative à la surface d'impresion dans le profil
	#
	#
	#def Refresh_Printing_surface(self):
	#	prtsurf = self.printing_surfaces[self.radio_box_3.GetSelection()]
	#	profile.putProfileSetting('printing_surface_name', prtsurf.name)
	#	profile.putProfileSetting('printing_surface_height', prtsurf.height)
	#	self.calculateZOffset()
		
	
	#fonction pour enregistrer les données relative à l'offset dans le profil
	#
	#
	def Refresh_Offset(self):
		valu = self.offset_ctrl.GetValue()
		if self.is_number(valu) :
			profile.putProfileSetting('offset_input', self.offset_ctrl.GetValue())
			self.calculateZOffset()
		else :
			self.offset_ctrl.SetValue(profile.getProfileSetting('offset_input'))
			self.offset_ctrl.Refresh()
		
	#fonction pour enregistrer les données relative au palpeur dans le profil
	#
	#
	def Refresh_Palpeur_chbx(self):
		if self.palpeur_chbx.GetValue():
			profile.putProfileSetting('palpeur_enable', self.palpeurs[0].palpeur)
		else:
			profile.putProfileSetting('palpeur_enable', self.palpeurs[1].palpeur)
			


	"""FIN ERIC"""


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

	"""ERIC"""
	# evenement sur le bloc Printing Surface
	# 
	# 
	def EVT_PrtSurf(self, event):
		self.Refresh_Printing_surface()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()


	# evenement sur le l'input pour l'Offset
	# 
	# 
	def EVT_Offset(self, event):
		self.Refresh_Offset()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()


	# evenement sur le bloc palpeur
	# 
	# 
	def EVT_Checkboxpalpeur(self, event):
		self.Refresh_Palpeur_chbx()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.updateProfileToControls()
		self.GetParent().GetParent().GetParent().scene.sceneUpdated()
		event.Skip()

	"""FIN ERIC"""




 	def Print_All(self):
		print '*******************************************'
		print 'Initialiastion'
		print "nozzle_size : ", profile.getProfileSetting('nozzle_size')
		print "rectration_enable : ", profile.getProfileSetting('retraction_enable')
		print "fan_full_height : ", profile.getProfileSetting('fan_full_height')
		print "fan_speed : ", profile.getProfileSetting('fan_speed')
		print "fan_speed_max : ", profile.getProfileSetting('fan_speed_max')
		print "coll_min_feedrate : ", profile.getProfileSetting('cool_min_feedrate')
		print '*******************************************'
		print "Filament : ", self.combo_box_1.GetStringSelection()
		print "filament_diameter : ", profile.getProfileSetting('filament_diameter')
		print "filament_flow : ", profile.getProfileSetting('filament_flow')
		print "Température de base : ", self.spin_ctrl_1.GetValue()
		print '*******************************************'
		print "Remplissage : ", self.radio_box_2.GetStringSelection()
		print "fill_density", profile.getProfileSetting('fill_density')
		print '*******************************************'
		print "Précision : ", self.radio_box_1.GetStringSelection()
		print "layer_height ", profile.getProfileSetting('layer_height')
		print "bottom_thickness / solid_layer_thickness : ", profile.getProfileSetting('solid_layer_thickness')
		print "shell_thickness / wall_thickness : ", profile.getProfileSetting('wall_thickness')
		print "print_speed : ", profile.getProfileSetting('print_speed')
		print "Print temp à add : ", self.temp_preci
		print "travel_speed : ", profile.getProfileSetting('travel_speed')
		print "bottom_layer_speed : ", profile.getProfileSetting('bottom_layer_speed')
		print "infill_speed : ", profile.getProfileSetting('infill_speed')
		print "inset0_speed : ", profile.getProfileSetting('inset0_speed')
		print "insetx_speed : ", profile.getProfileSetting('insetx_speed')
		print '*******************************************'
		print "Support Label : ", doc.getElementsByTagName("Bloc_Support")[0].getAttribute("label")
		print "support : ", profile.getProfileSetting('support')
		print "platform_adhesion : ", profile.getProfileSetting('platform_adhesion')
		print '*******************************************'
		print "Température d'impression : ", profile.getProfileSetting('print_temperature')
		"""ERIC"""
		print '*******************************************'
		print "Surface d'impression choisie : "
		print "name : ", profile.getProfileSetting('printing_surface_name')
		print "height : ", profile.getProfileSetting('printing_surface_height')
		print '*******************************************'
		print "Offset en Z : "
		print "Valeur Entrée : ", profile.getProfileSetting('offset_input')
		print "Valeur Calculée : ", profile.getProfileSetting('offset_value')
		print '*******************************************'
		print "Palpeur Activé: ", profile.getProfileSetting('palpeur_enable')
		print '*******************************************'
		"""FIN ERIC"""


	def Click_Button(self, event):
		profile.putProfileSetting('print_temperature', str(self.spin_ctrl_1.GetValue() + self.temp_preci))
		self.Print_All()
		profile.saveProfile(profile.getDefaultProfilePath(), True)
		self.GetParent().GetParent().GetParent().scene.OnPrintButton(1)		
		event.Skip()
		
	def _addSettingsToPanels(self, category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, _(title))
			for s in profile.getSettingsForCategory(category, title):
				configBase.SettingRow(p, s.getName())

	def SizeLabelWidths(self, left, right):
		leftWidth = self.getLabelColumnWidth(left)
		rightWidth = self.getLabelColumnWidth(right)
		maxWidth = max(leftWidth, rightWidth)
		self.setLabelColumnWidth(left, maxWidth)
		self.setLabelColumnWidth(right, maxWidth)

	def OnSize(self, e):
		e.Skip()

	def UpdateSize(self, configPanel):
		sizer = configPanel.GetSizer()

		# Pseudocde
		# if horizontal:
		#     if width(col1) < best_width(col1) || width(col2) < best_width(col2):
		#         switch to vertical
		# else:
		#     if width(col1) > (best_width(col1) + best_width(col1)):
		#         switch to horizontal
		#

		col1 = configPanel.leftPanel
		colSize1 = col1.GetSize()
		colBestSize1 = col1.GetBestSize()
		col2 = configPanel.rightPanel
		colSize2 = col2.GetSize()
		colBestSize2 = col2.GetBestSize()

		orientation = sizer.GetOrientation()

		if orientation == wx.HORIZONTAL:
			if (colSize1[0] <= colBestSize1[0]) or (colSize2[0] <= colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.VERTICAL)
				sizer.Add(configPanel.leftPanel, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()
		else:
			if max(colSize1[0], colSize2[0]) > (colBestSize1[0] + colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.HORIZONTAL)
				sizer.Add(configPanel.leftPanel, proportion=1, border=35, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, proportion=1, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()

	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		# if self.alterationPanel is not None:
		# 	self.alterationPanel.updateProfileToControls()
		# self.pluginPanel.updateProfileToControls()
