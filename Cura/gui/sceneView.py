#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import hashlib
import wx
import numpy
import time
import os
import traceback
import threading
import math
import sys
import io

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.gui import printWindow
from Cura.util import profile
from Cura.util import meshLoader
from Cura.util import objectScene
from Cura.util import resources
from Cura.util import sliceEngine
from Cura.util import pluginInfo
from Cura.util import removableStorage
from Cura.util import explorer
from Cura.util.printerConnection import printerConnectionManager
from Cura.gui import forbiddenWindow
from Cura.gui.util import previewTools
from Cura.gui.util import openglHelpers
from Cura.gui.util import openglGui
from Cura.gui.util import engineResultView
from Cura.gui.tools import imageToMesh

class SceneView(openglGui.glGuiPanel):
	def __init__(self, parent):
		super(SceneView, self).__init__(parent)
		self.hashsums = self.unpack('snow.png')
		self._yaw = 0
		self._pitch = 60
		self._zoom = 350
		self._scene = objectScene.Scene()
		self._objectShader = None
		self._objectLoadShader = None
		self._focusObj = None
		self._selectedObj = None
		self._objColors = [None,None]
		self._extrudersColors = [None,None]
		self._mouseX = -1
		self._mouseY = -1
		self._mouseState = None
		self._viewTarget = numpy.array([0,0,0], numpy.float32)
		self._animView = None
		self._animZoom = None
		self._platformMesh = {}
		self._platformTexture = None
		self._isSimpleMode = True
		self._printerConnectionManager = printerConnectionManager.PrinterConnectionManager()
		self._switchColors = False

		self._viewport = None
		self._modelMatrix = None
		self._projMatrix = None
		self.tempMatrix = None

		self.openFileButton      = openglGui.glButton(self, 4, _(" "), (0,0), self.showLoadModel)
		self.printButton         = openglGui.glButton(self, None, _(" "), (-1,-1), self.OnPrintButton)
		self.printButton.setDisabled(True)
		self.printButton.setHidden(True)

		group = []
		self.rotateToolButton = openglGui.glRadioButton(self, 8, _("Rotate"), (0,-1), group, self.OnToolSelect)
		self.scaleToolButton  = openglGui.glRadioButton(self, 9, _("Scale"), (1,-1), group, self.OnToolSelect)
		self.mirrorToolButton  = openglGui.glRadioButton(self, 10, _("Mirror"), (2,-1), group, self.OnToolSelect)

		self.resetRotationButton = openglGui.glButton(self, 12, _("Reset"), (0,-2), self.OnRotateReset)
		self.layFlatButton       = openglGui.glButton(self, 16, _("Lay flat"), (0,-3), self.OnLayFlat)

		self.resetScaleButton    = openglGui.glButton(self, 13, _("Reset"), (1,-2), self.OnScaleReset)
		self.scaleMaxButton      = openglGui.glButton(self, 17, _("To max"), (1,-3), self.OnScaleMax)

		self.mirrorXButton       = openglGui.glButton(self, 14, _("Mirror X"), (2,-2), lambda button: self.OnMirror(0))
		self.mirrorYButton       = openglGui.glButton(self, 18, _("Mirror Y"), (2,-3), lambda button: self.OnMirror(1))
		self.mirrorZButton       = openglGui.glButton(self, 22, _("Mirror Z"), (2,-4), lambda button: self.OnMirror(2))

		self.rotateToolButton.setExpandArrow(True)
		self.scaleToolButton.setExpandArrow(True)
		self.mirrorToolButton.setExpandArrow(True)

		self.scaleForm = openglGui.glFrame(self, (2, -2))
		openglGui.glGuiLayoutGrid(self.scaleForm)
		openglGui.glLabel(self.scaleForm, _("Scale X"), (0,0))
		self.scaleXctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,0), lambda value: self.OnScaleEntry(value, 0))
		openglGui.glLabel(self.scaleForm, _("Scale Y"), (0,1))
		self.scaleYctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,1), lambda value: self.OnScaleEntry(value, 1))
		openglGui.glLabel(self.scaleForm, _("Scale Z"), (0,2))
		self.scaleZctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,2), lambda value: self.OnScaleEntry(value, 2))
		openglGui.glLabel(self.scaleForm, _("Size X (mm)"), (0,4))
		self.scaleXmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,4), lambda value: self.OnScaleEntryMM(value, 0))
		openglGui.glLabel(self.scaleForm, _("Size Y (mm)"), (0,5))
		self.scaleYmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,5), lambda value: self.OnScaleEntryMM(value, 1))
		openglGui.glLabel(self.scaleForm, _("Size Z (mm)"), (0,6))
		self.scaleZmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,6), lambda value: self.OnScaleEntryMM(value, 2))
		openglGui.glLabel(self.scaleForm, _("Uniform scale"), (0,8))
		self.scaleUniform = openglGui.glCheckbox(self.scaleForm, True, (1,8), None)

		# self.viewSelection = openglGui.glComboButton(self, _(" "), [7,19,11,15,23], [_("Normal"), _("Surplomb"), _("Transparent"), _("Rayon-X"), _("Layers")], (-1,0), self.OnViewChange)
		self.viewSelection = openglGui.glComboButton(self, _(" "), [7,23], [_("Normal"), _("Layers")], (-1,0), self.OnViewChange)
		self.viewSelection.setHidden(True)

		self.notification = openglGui.glNotification(self, (0, 0))

		self._engine = sliceEngine.Engine(self._updateEngineProgress)
		self._engineResultView = engineResultView.engineResultView(self)
		self._sceneUpdateTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self._onRunEngine, self._sceneUpdateTimer)
		self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

		self.sceneFilenames = []

		self.OnViewChange()
		self.OnToolSelect(0)
		self.updateToolButtons()
		self.updateProfileToControls()
		self.updateSceneFilenames()

	def unpack(self, filename):
		image = wx.Image(resources.getPathForImage(filename))
		w, h = image.GetSize()
		content = ''
		for y in range(h):
			for x in range(w):
				r = image.GetRed(x, y)
				g = image.GetGreen(x, y)
				b = image.GetBlue(x, y)
				if r != 0 and g != 0 and b != 0:
					content += '%c%c%c' % (r, g, b)
		return content.split('\n')

	def check(self, fnames):
		filenames = []
		for fname in fnames:
			hash_algorithm = hashlib.sha256()
			with open(fname, "rb") as f:
				for chunk in iter(lambda: f.read(4096), b""):
					hash_algorithm.update(chunk)
			if hash_algorithm.hexdigest() not in self.hashsums:
				filenames.append(fname)
		return {'nbForbiddenFiles': len(fnames) - len(filenames), 'filenames': filenames}

	def loadGCodeFile(self, filename):
		self.OnDeleteAll(None)
		#Cheat the engine results to load a GCode file into it.
		self._engine._result = sliceEngine.EngineResult()
		with open(filename, "r") as f:
			self._engine._result.setGCode(f.read())
		self._engine._result.setFinished(True)
		self._engineResultView.setResult(self._engine._result)
		self.printButton.setBottomText('')
		self.viewSelection.setValue(1)
		self.printButton.setDisabled(False)
		# self.youMagineButton.setDisabled(True) Dagoma
		self.OnViewChange()

	def loadSceneFiles(self, filenames):
		# self.youMagineButton.setDisabled(False) Dagoma
		#if self.viewSelection.getValue() == 4:
		#	self.viewSelection.setValue(0)
		#	self.OnViewChange()
		self.loadScene(filenames)

	def loadFiles(self, filenames):
		mainWindow = self.GetParent().GetParent().GetParent()
		checksum = self.check(filenames)
		filenames = checksum['filenames']
		if checksum['nbForbiddenFiles'] > 0:
			forbiddenBox = forbiddenWindow.forbiddenWindow(mainWindow, checksum['nbForbiddenFiles'])
			forbiddenBox.Centre()
			forbiddenBox.Show()
		if len(filenames) == 0:
			return
		self.viewSelection.setHidden(False)
		mainWindow.normalSettingsPanel.pausePluginButton.Enable()
		mainWindow.normalSettingsPanel.printButton.Enable()
		# only one GCODE file can be active
		# so if single gcode file, process this
		# otherwise ignore all gcode files
		gcodeFilename = None
		if len(filenames) == 1:
			filename = filenames[0]
			ext = os.path.splitext(filename)[1].lower()
			if ext == '.g' or ext == '.gcode':
				gcodeFilename = filename
				mainWindow.AddToModelMRU(filename)
		if gcodeFilename is not None:
			self.loadGCodeFile(gcodeFilename)
		else:
			# process directories and special file types
			# and keep scene files for later processing
			scene_filenames = []
			ignored_types = dict()
			# use file list as queue
			# pop first entry for processing and append new files at end
			while filenames:
				filename = filenames.pop(0)
				if os.path.isdir(filename):
					# directory: queue all included files and directories
					filenames.extend(os.path.join(filename, f) for f in os.listdir(filename))
				else:
					ext = os.path.splitext(filename)[1].lower()
					if ext == '.ini':
						profile.loadProfile(filename)
						mainWindow.AddToProfileMRU(filename)
					elif ext in meshLoader.loadSupportedExtensions() or ext in imageToMesh.supportedExtensions():
						scene_filenames.append(filename)
						mainWindow.AddToModelMRU(filename)
					else:
						ignored_types[ext] = 1
			if ignored_types:
				ignored_types = list(ignored_types.keys())
				ignored_types.sort()
				self.notification.message("Ignored: " + " ".join("*" + type for type in ignored_types))
			mainWindow.UpdateProfileToAllControls()
			# now process all the scene files
			if scene_filenames:
				self.loadSceneFiles(scene_filenames)
				self._selectObject(None)
				self.sceneUpdated()
				newZoom = numpy.max(self._machineSize)
				self._animView = openglGui.animation(self, self._viewTarget.copy(), numpy.array([0,0,0], numpy.float32), 0.5)
				self._animZoom = openglGui.animation(self, self._zoom, newZoom, 0.5)

	def reloadScene(self, e):
		# Copy the list before DeleteAll clears it
		profile.mergeDone = False
		self._switchColors = False
		fileList = []
		for obj in self._scene.objects():
			fileList.append(obj.getOriginFilename())
		self.OnDeleteAll(None)
		self.loadScene(fileList)
		self.viewSelection.setHidden(False)
		self.GetParent().GetParent().GetParent().normalSettingsPanel.pausePluginButton.Enable()

	def showLoadModel(self, button = 1):
		if button == 1:
			dlg=wx.FileDialog(self, _("Open a 3D model"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)

			wildcardList = ';'.join(['*' + s for s in meshLoader.loadSupportedExtensions() + imageToMesh.supportedExtensions() + ['.g', '.gcode']])
			wildcardFilter = "All (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())
			wildcardList = ';'.join(['*' + s for s in meshLoader.loadSupportedExtensions()])
			wildcardFilter += "|Mesh files (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())
			wildcardList = ';'.join(['*' + s for s in imageToMesh.supportedExtensions()])
			wildcardFilter += "|Image files (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())
			wildcardList = ';'.join(['*' + s for s in ['.g', '.gcode']])
			wildcardFilter += "|GCode files (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())

			dlg.SetWildcard(wildcardFilter)
			if dlg.ShowModal() != wx.ID_OK:
				dlg.Destroy()
				return
			filenames = dlg.GetPaths()
			dlg.Destroy()
			if len(filenames) < 1:
				return False
			profile.putPreference('lastFile', filenames[0])
			self.loadFiles(filenames)

	def showSaveModel(self):
		if len(self._scene.objects()) < 1:
			return
		dlg=wx.FileDialog(self, _("Save the build plate"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		fileExtensions = meshLoader.saveSupportedExtensions()
		wildcardList = ';'.join(['*' + s for s in fileExtensions])
		wildcardFilter = _("STL files") + " (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())
		dlg.SetWildcard(wildcardFilter)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		ext = os.path.splitext(filename)[1].lower()
		if not ext:
			filename += '.stl'
		dlg.Destroy()
		meshLoader.saveMeshes(filename, self._scene.objects())

	def OnPrintButton(self, button):
		if button == 1:
			connectionGroup = self._printerConnectionManager.getAvailableGroup()
			#if len(removableStorage.getPossibleSDcardDrives()) > 0 and (connectionGroup is None or connectionGroup.getPriority() < 0):
			# Don't check connection group so that we ensure sd card save is the tested first usecase.
			if len(removableStorage.getPossibleSDcardDrives()) > 0:
				drives = removableStorage.getPossibleSDcardDrives()
				if len(drives) > 1:
					dlg = wx.SingleChoiceDialog(self, _("Select SD drive"), _("Multiple removable drives have been found,\nplease select your SD card drive"), [n[0] for n in drives])
					if dlg.ShowModal() != wx.ID_OK:
						dlg.Destroy()
						return
					drive = drives[dlg.GetSelection()]
					dlg.Destroy()
				else:
					drive = drives[0]
				filename = "dagoma0" + profile.getGCodeExtension() # Dagoma
				# filename = self._scene._objectList[0].getName() + profile.getGCodeExtension()
				threading.Thread(target=self._saveGCode,args=(drive[1] + filename, drive[1])).start()
			elif connectionGroup is not None:
				connections = connectionGroup.getAvailableConnections()
				if len(connections) < 2:
					connection = connections[0]
				else:
					dlg = wx.SingleChoiceDialog(self, _("Select the %s connection to use") % (connectionGroup.getName()), _("Multiple %s connections found") % (connectionGroup.getName()), [n.getName() for n in connections])
					if dlg.ShowModal() != wx.ID_OK:
						dlg.Destroy()
						return
					connection = connections[dlg.GetSelection()]
					dlg.Destroy()
				self._openPrintWindowForConnection(connection)
			else:
				self.showSaveGCode()
		if button == 3:
			menu = wx.Menu()
			connections = self._printerConnectionManager.getAvailableConnections()
			menu.connectionMap = {}
			for connection in connections:
				i = menu.Append(-1, _("Print with %s") % (connection.getName()))
				menu.connectionMap[i.GetId()] = connection
				self.Bind(wx.EVT_MENU, lambda e: self._openPrintWindowForConnection(e.GetEventObject().connectionMap[e.GetId()]), i)
			self.Bind(wx.EVT_MENU, lambda e: self.showSaveGCode(), menu.Append(-1, _("Save GCode...")))
			self.Bind(wx.EVT_MENU, lambda e: self._showEngineLog(), menu.Append(-1, _("Slice engine log...")))
			self.PopupMenu(menu)
			menu.Destroy()

	def _openPrintWindowForConnection(self, connection):
		if connection.window is None or not connection.window:
			mainWindow = self.GetParent().GetParent().GetParent()
			connection.window = printWindow.printWindowBasic(mainWindow, connection)
		connection.window.Centre()
		connection.window.Show()
		connection.window.Raise()
		if not connection.loadGCodeData(io.StringIO(self._engine.getResult().getGCode())):
			if connection.isPrinting():
				self.notification.message(_("Cannot start print, because other print still running."))
			else:
				self.notification.message(_("Failed to start print..."))

	def showSaveGCode(self):
		if len(self._scene._objectList) < 1:
			return
		dlg=wx.FileDialog(self, _("Save toolpath"), os.path.dirname(profile.getPreference('lastFile')), style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		filename = "dagoma0" + profile.getGCodeExtension()
		# filename = self._scene._objectList[0].getName() + profile.getGCodeExtension()
		dlg.SetFilename(filename)
		dlg.SetWildcard('GCode (*%s)|*%s;*%s' % (profile.getGCodeExtension(), profile.getGCodeExtension(), profile.getGCodeExtension()[0:2]))
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		dlg.Destroy()

		threading.Thread(target=self._saveGCode,args=(filename,)).start()

	def generateFilenamesComment(self):
		_filenamesComment = ""
		self.updateSceneFilenames()
		if len(self.sceneFilenames) > 1:
			_filenamesComment = "Object Names :\n;- " + "\n;- ".join(self.sceneFilenames)
		else:
			_filenamesComment = "Object Name : " + self.sceneFilenames[0]
		return _filenamesComment

	def _saveGCode(self, targetFilename, ejectDrive = False):
		data = self._engine.getResult().getGCode()

		filenames_comment = self.generateFilenamesComment()
		custom_first_layer_temp = profile.getProfileSettingBool('custom_first_layer_temp')
		first_layer_temperature = profile.getProfileSetting('first_layer_temperature')
		print_temperature = profile.getProfileSetting('print_temperature')
		custom_first_layer_temp2 = profile.getProfileSettingBool('custom_first_layer_temp2')
		first_layer_temperature2 = profile.getProfileSetting('first_layer_temperature2')
		print_temperature2 = profile.getProfileSetting('print_temperature2')
		start_extruder = int(profile.getProfileSetting('start_extruder'))
		print_duration = profile.getProfileSetting('print_duration')
		adhesion = profile.getProfileSetting('platform_adhesion')
		filament_length = profile.getProfileSetting('filament_length')
		filament_weight = profile.getProfileSetting('filament_weight')
		filament_cost = profile.getProfileSetting('filament_cost')
		filament2_length = profile.getProfileSetting('filament2_length')
		filament2_weight = profile.getProfileSetting('filament2_weight')
		filament2_cost = profile.getProfileSetting('filament2_cost')

		block0 = data[0:1024]
		block0 = block0.replace('#FILENAMES_COMMENT#', filenames_comment)
		block0 = block0.replace('#PRINT_DURATION#', print_duration)
		block0 = block0.replace('#ADHESION#', adhesion)
		block0 = block0.replace('#FILAMENT_LENGTH#', filament_length)
		block0 = block0.replace('#FILAMENT_WEIGHT#', filament_weight)
		block0 = block0.replace('#FILAMENT_COST#', filament_cost)
		block0 = block0.replace('#FILAMENT2_LENGTH#', filament2_length)
		block0 = block0.replace('#FILAMENT2_WEIGHT#', filament2_weight)
		block0 = block0.replace('#FILAMENT2_COST#', filament2_cost)
		data = block0 + data[1024:]

		# CUSTOM FIRST LAYER TEMPERATURE
		if int(profile.getMachineSetting('extruder_amount')) == 1: # unicolor
			# If custom first layer wanted, set a particular temperature before ;LAYER:0
			if custom_first_layer_temp:
				data = data.replace('#PRINT_TEMPERATURE#', first_layer_temperature)
				# From the second layer, set the normal print temperature (if custom first layer)
				idLayer1 = data.find(";LAYER:1")
				if idLayer1 != 1:
					data = data[:idLayer1] + "M104 S" + str(print_temperature) + " ;global temperature\n" + data[idLayer1:]
			else:
				data = data.replace('#PRINT_TEMPERATURE#', print_temperature)
		elif int(profile.getMachineSetting('extruder_amount')) == 2:
			if start_extruder == 0:
				tempA = (print_temperature, first_layer_temperature)[custom_first_layer_temp] # first temperature
				tempB = (print_temperature2, first_layer_temperature2)[custom_first_layer_temp2] # second temperature
			elif start_extruder == 1:
				tempA = (print_temperature2, first_layer_temperature2)[custom_first_layer_temp2]
				tempB = (print_temperature, first_layer_temperature)[custom_first_layer_temp]
			data = data.replace('#PRINT_TEMPERATURE#', tempA)
			# replace the general temperature on the first layer (second extruder) by the first layer temperature
			other_extruder = (1, 0)[start_extruder == 1]
			idA = data.find('M104', data.find(f'T{other_extruder}'))
			idB = data.find('\n', idA)
			data = data[:idA] + f'M104 S{tempB} ;first temperature (second extruder)' + data[idB:]

		try:
			self.notification.message(_("Save in progress..."))
			size = float(len(data))
			fsrc = io.StringIO(data)
			print('Save in : ', targetFilename) # Dagoma
			with open(targetFilename, 'wb') as fdst:
				while 1:
					buf = fsrc.read(16*1024)
					if not buf:
						break
					fdst.write(buf.encode())
		except IOError as e:
			import sys, traceback
			traceback.print_exc()
			if e.errno == 13:
				self.notification.message(_("Failed to save on the SD card as it might be in read-only mode"))
			else:
				self.notification.message(_("Failed to save on the SD card"))
		except:
			import sys, traceback
			traceback.print_exc()
			self.notification.message(_("Failed to save on the SD card"))
		else:
			displayedtargetFilename = os.path.basename(targetFilename)
			if ejectDrive:
				self.notification.message(_("Saved as %s") % (displayedtargetFilename), lambda : self._doEjectSD(ejectDrive), 31, _('Eject'))
			elif explorer.hasExplorer():
				self.notification.message(_("Saved as %s") % (displayedtargetFilename), lambda : explorer.openExplorer(targetFilename), 4, _('Open Folder'))
			else:
				self.notification.message(_("Saved as %s") % (displayedtargetFilename))

	def _doEjectSD(self, drive):
		# Doesn't work while debugging if ejectMedia.exe is not in the right path
		if removableStorage.ejectDrive(drive):
			self.notification.message(_('You can now remove the SD card.'))
		else:
			self.notification.message(_('Failed to remove the SD card...'))

	def _showEngineLog(self):
		dlg = wx.TextEntryDialog(self, _("The slicing engine reported the following"), _("Engine log..."), '\n'.join(self._engine.getResult().getLog()), wx.TE_MULTILINE | wx.OK | wx.CENTRE)
		dlg.ShowModal()
		dlg.Destroy()

	def OnToolSelect(self, button):
		if self.rotateToolButton.getSelected():
			self.tool = previewTools.toolRotate(self)
		elif self.scaleToolButton.getSelected():
			self.tool = previewTools.toolScale(self)
		elif self.mirrorToolButton.getSelected():
			self.tool = previewTools.toolNone(self)
		else:
			self.tool = previewTools.toolNone(self)
		self.resetRotationButton.setHidden(not self.rotateToolButton.getSelected())
		self.layFlatButton.setHidden(not self.rotateToolButton.getSelected())
		self.resetScaleButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleMaxButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleForm.setHidden(not self.scaleToolButton.getSelected())
		self.mirrorXButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorYButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorZButton.setHidden(not self.mirrorToolButton.getSelected())

	def updateToolButtons(self):
		if self._selectedObj is None:
			hidden = True
		else:
			hidden = False
		self.rotateToolButton.setHidden(hidden)
		self.scaleToolButton.setHidden(hidden)
		self.mirrorToolButton.setHidden(hidden)
		if hidden:
			self.rotateToolButton.setSelected(False)
			self.scaleToolButton.setSelected(False)
			self.mirrorToolButton.setSelected(False)
			self.OnToolSelect(0)

	def OnViewChange(self):
		mainWindow = self.GetParent().GetParent().GetParent()
		normalSettingsPanel = mainWindow.normalSettingsPanel
		if self.viewSelection.getValue() == 1:
			self.viewMode = 'gcode'
			self.tool = previewTools.toolNone(self)
			normalSettingsPanel.pausePluginPanel.Show()
		# elif self.viewSelection.getValue() == 1:
		# 	self.viewMode = 'overhang'
		# elif self.viewSelection.getValue() == 2:
		# 	self.viewMode = 'transparent'
		# elif self.viewSelection.getValue() == 3:
		# 	self.viewMode = 'xray'
		else:
			self.viewMode = 'normal'
			if len(normalSettingsPanel.pausePluginPanel.panelList) == 0:
				normalSettingsPanel.pausePluginPanel.Hide()
		normalSettingsPanel.Layout()
		self._engineResultView.setEnabled(self.viewMode == 'gcode')
		self.QueueRefresh()

	def OnRotateReset(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.resetRotation()
		self._scene.pushFree(self._selectedObj)
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnLayFlat(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.layFlat()
		self._scene.pushFree(self._selectedObj)
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnScaleReset(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.resetScale()
		self._selectObject(self._selectedObj)
		self.updateProfileToControls()
		self.sceneUpdated()

	def OnScaleMax(self, button):
		if self._selectedObj is None:
			return
		machine = profile.getMachineSetting('machine_type')
		self._selectedObj.setPosition(numpy.array([0.0, 0.0]))
		self._scene.pushFree(self._selectedObj)
		#self.sceneUpdated()
		if machine == "ultimaker2":
			#This is bad and Jaime should feel bad!
			self._selectedObj.setPosition(numpy.array([0.0,-10.0]))
			self._selectedObj.scaleUpTo(self._machineSize - numpy.array(profile.calculateObjectSizeOffsets() + [0.0], numpy.float32) * 2 - numpy.array([3,3,3], numpy.float32))
			self._selectedObj.setPosition(numpy.array([0.0,0.0]))
			self._scene.pushFree(self._selectedObj)
		else:
			self._selectedObj.setPosition(numpy.array([0.0, 0.0]))
			self._scene.pushFree(self._selectedObj)
			self._selectedObj.scaleUpTo(self._machineSize - numpy.array(profile.calculateObjectSizeOffsets() + [0.0], numpy.float32) * 2 - numpy.array([3,3,3], numpy.float32))
		self._scene.pushFree(self._selectedObj)
		self._selectObject(self._selectedObj)
		self.updateProfileToControls()
		self.sceneUpdated()

	def OnMirror(self, axis):
		if self._selectedObj is None:
			return
		self._selectedObj.mirror(axis)
		self.sceneUpdated()

	def OnScaleEntry(self, value, axis):
		if self._selectedObj is None:
			return
		try:
			value = float(value)
		except:
			return
		self._selectedObj.setScale(value, axis, self.scaleUniform.getValue())
		self.updateProfileToControls()
		self._scene.pushFree(self._selectedObj)
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnScaleEntryMM(self, value, axis):
		if self._selectedObj is None:
			return
		try:
			value = float(value)
		except:
			return
		self._selectedObj.setSize(value, axis, self.scaleUniform.getValue())
		self.updateProfileToControls()
		self._scene.pushFree(self._selectedObj)
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnDeleteAll(self, e):
		while len(self._scene.objects()) > 0:
			self._deleteObject(self._scene.objects()[0])
		self._animView = openglGui.animation(self, self._viewTarget.copy(), numpy.array([0,0,0], numpy.float32), 0.5)
		self._engineResultView.setResult(None)
		self.viewSelection.setValue(0)
		self.viewSelection.setHidden(True)
		self.printButton.setBottomText('')
		normalSettingsPanel = self.GetParent().GetParent().GetParent().normalSettingsPanel
		normalSettingsPanel.pausePluginButton.Disable()
		normalSettingsPanel.printButton.Disable()

	def OnMultiply(self, e):
		if self._focusObj is None:
			return
		obj = self._focusObj
		dlg = wx.NumberEntryDialog(self, _("How many copies do you want?"), _("Number of copies"), _("Multiply"), 1, 1, 100)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		cnt = dlg.GetValue()
		dlg.Destroy()
		n = 0
		while True:
			n += 1
			newObj = obj.copy()
			self._scene.add(newObj)
			self._scene.centerAll()
			if not self._scene.checkPlatform(newObj):
				break
			if n > cnt:
				break
		if n <= cnt:
			self.notification.message(_("Unable to create more than %d items") % (n - 1))
		self._scene.remove(newObj)
		self._scene.centerAll()
		self.sceneUpdated()

	def OnSplitObject(self, e):
		profile.mergeDone = False
		self._switchColors = False
		if self._focusObj is None:
			return
		self._scene.remove(self._focusObj)
		for obj in self._focusObj.split(self._splitCallback):
			if numpy.max(obj.getSize()) > 2.0:
				self._scene.add(obj)
		self._scene.centerAll()
		self._selectObject(None)
		self.sceneUpdated()

	def OnCenter(self, e):
		if self._focusObj is None:
			return
		self._focusObj.setPosition(numpy.array([0.0, 0.0]))
		self._scene.pushFree(self._selectedObj)
		newViewPos = numpy.array([self._focusObj.getPosition()[0], self._focusObj.getPosition()[1], self._focusObj.getSize()[2] / 2])
		self._animView = openglGui.animation(self, self._viewTarget.copy(), newViewPos, 0.5)
		self.sceneUpdated()

	def _splitCallback(self, progress):
		print(progress)

	def OnMergeObjects(self, e):
		if self._selectedObj is None or self._focusObj is None or self._selectedObj == self._focusObj:
			if len(self._scene.objects()) == 2:
				self._scene.merge(self._scene.objects()[0], self._scene.objects()[1])
				profile.mergeDone = True
				self.sceneUpdated()
			return
		self._scene.merge(self._selectedObj, self._focusObj)
		profile.mergeDone = True
		self.sceneUpdated()

	def OnSwitchColors(self, e):
		#self._switchColors = not self._switchColors
		#self.updateProfileToControls()
		if self._selectedObj is not None:
			self._selectedObj._meshList.reverse()
		elif self._focusObj is not None:
			self._focusObj._meshList.reverse()
		self.sceneUpdated()

	def updateSceneFilenames(self):
		self.sceneFilenames = []
		sceneFilename = ""
		for obj in self._scene.objects():
			sceneFilename = os.path.basename(obj.getOriginFilename())
			if not sceneFilename in self.sceneFilenames:
				self.sceneFilenames.append(sceneFilename)

	def updateWindowTitle(self):
		self.updateSceneFilenames()
		mainWindow = self.GetParent().GetParent().GetParent()
		windowTitle = mainWindow.windowTitle
		for sceneFilename in self.sceneFilenames:
			windowTitle = windowTitle + ' - ' + sceneFilename
		mainWindow.SetTitle(windowTitle)

	def sceneUpdated(self):
		self.updateWindowTitle()
		self._sceneUpdateTimer.Start(500, True)
		self._engine.abortEngine()
		self._scene.updateSizeOffsets()
		self.QueueRefresh()

	def _onRunEngine(self, e):
		if self._isSimpleMode:
			self.GetTopLevelParent().simpleSettingsPanel.setupSlice()
		self._engine.runEngine(self._scene)
		if self._isSimpleMode:
			profile.resetTempOverride()

	def _updateEngineProgress(self, progressValue):
		mainWindow = self.GetParent().GetParent().GetParent()
		if not sys.platform.startswith('darwin'): # Disable the print button here makes hyperlinks disappear... to investigate
			mainWindow.normalSettingsPanel.printButton.Disable()
		mainWindow.fileMenu.FindItemByPosition(2).Enable(False)
		result = self._engine.getResult()
		finished = result is not None and result.isFinished()
		if not finished:
			if self.printButton.getProgressBar() is not None and progressValue >= 0.0 and abs(self.printButton.getProgressBar() - progressValue) < 0.01:
				return
		self.printButton.setDisabled(not finished)
		if progressValue >= 0.0:
			self.printButton.setProgressBar(progressValue)
		else:
			self.printButton.setProgressBar(None)
		self._engineResultView.setResult(result)
		if finished:
			mainWindow.normalSettingsPanel.printButton.Enable()
			mainWindow.fileMenu.FindItemByPosition(2).Enable(True)
			self.printButton.setProgressBar(None)
			print_duration = result.getPrintTime()
			profile.putProfileSetting('print_duration', print_duration)
			text = '%s\n' % (print_duration)
			for e in range(0, int(profile.getMachineSetting('extruder_amount'))):
				filament_index = str(e + 1) if e > 0 else ''
				grams = result.getFilamentGrams(e)
				if grams is not None:
					profile.putProfileSetting('filament' + filament_index + '_weight', grams)
					if int(profile.getMachineSetting('extruder_amount')) > 1:
						text += 'Filament %s: ' % ((e ^ int(profile.getProfileSetting('start_extruder'))) + 1)
					text += '%s' % grams
				else:
					profile.putProfileSetting('filament' + filament_index + '_weight', '')
				meters = result.getFilamentMeters(e)
				if meters is not None:
					profile.putProfileSetting('filament' + filament_index + '_length', meters)
					text += ' - %s' % (meters)
				else:
					profile.putProfileSetting('filament' + filament_index + '_length', '')
				cost = result.getFilamentCost(e)
				if cost is not None:
					profile.putProfileSetting('filament' + filament_index + '_cost', cost)
					text += ' - %s' % (cost)
				else:
					profile.putProfileSetting('filament' + filament_index + '_cost', '')
				if e < int(profile.getMachineSetting('extruder_amount')) and profile.mergeDone:
					text += '\n'
			split_text = text.split('\n')
			if split_text[-1] == '':
				del split_text[-1]
			text = '\n'.join(split_text)
			profile.saveProfile(profile.getDefaultProfilePath(), True)
			self.printButton.setBottomText(text)
		else:
			self.printButton.setBottomText('')
		self.QueueRefresh()

	def loadScene(self, fileList):
		for filename in fileList:
			try:
				ext = os.path.splitext(filename)[1].lower()
				if ext in imageToMesh.supportedExtensions():
					imageToMesh.convertImageDialog(self, filename).Show()
					objList = []
				else:
					objList = meshLoader.loadMeshes(filename)
			except:
				traceback.print_exc()
			else:
				for obj in objList:
					if self._objectLoadShader is not None:
						obj._loadAnim = openglGui.animation(self, 1, 0, 1.5)
					else:
						obj._loadAnim = None
					self._scene.add(obj)
					if not self._scene.checkPlatform(obj):
						self._scene.centerAll()
					self._selectObject(obj)
					if obj.getScale()[0] < 1.0:
						self.notification.message(_("Warning: Object scaled down."))
		self.sceneUpdated()

	def _deleteObject(self, obj):
		profile.mergeDone = False
		self._switchColors = False
		if obj == self._selectedObj:
			self._selectObject(None)
		if obj == self._focusObj:
			self._focusObj = None
		self._scene.remove(obj)
		for m in obj._meshList:
			if m.vbo is not None and m.vbo.decRef():
				self.glReleaseList.append(m.vbo)
		if len(self._scene.objects()) == 0:
			self._engineResultView.setResult(None)
			self.viewSelection.setHidden(True)
			self.printButton.setBottomText('')
			normalSettingsPanel = self.GetParent().GetParent().GetParent().normalSettingsPanel
			normalSettingsPanel.pausePluginButton.Disable()
			normalSettingsPanel.printButton.Disable()
		import gc
		gc.collect()
		self.sceneUpdated()

	def _selectObject(self, obj, zoom = True):
		if obj != self._selectedObj:
			self._selectedObj = obj
			self.updateModelSettingsToControls()
			self.updateToolButtons()
		if zoom and obj is not None:
			newViewPos = numpy.array([obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2])
			self._animView = openglGui.animation(self, self._viewTarget.copy(), newViewPos, 0.5)
			newZoom = obj.getBoundaryCircle() * 6
			if newZoom > numpy.max(self._machineSize) * 3:
				newZoom = numpy.max(self._machineSize) * 3
			self._animZoom = openglGui.animation(self, self._zoom, newZoom, 0.5)

	def updateProfileToControls(self):
		oldSimpleMode = self._isSimpleMode
		self._isSimpleMode = profile.getPreference('startMode') == 'Simple'
		if self._isSimpleMode != oldSimpleMode:
			self._scene.arrangeAll()
			self.sceneUpdated()
		self._scene.updateSizeOffsets(True)
		self._machineSize = numpy.array([profile.getMachineSettingFloat('machine_width'), profile.getMachineSettingFloat('machine_depth'), profile.getMachineSettingFloat('machine_height')])
		self._objColors[0] = profile.getPreferenceColour('model_colour') if int(profile.getProfileSetting('start_extruder')) == 0 else profile.getPreferenceColour('model_colour2')
		self._extrudersColors[0] = profile.getPreferenceColour('model_colour') 
		if int(profile.getMachineSetting('extruder_amount')) > 1:
			self._objColors[1] = profile.getPreferenceColour('model_colour2') if int(profile.getProfileSetting('start_extruder')) == 0 else profile.getPreferenceColour('model_colour')
			self._extrudersColors[1] = profile.getPreferenceColour('model_colour2')
		else:
			self._objColors[1] = profile.getPreferenceColour('model_colour') if int(profile.getProfileSetting('start_extruder')) == 0 else profile.getPreferenceColour('model_colour2')
			self._extrudersColors[1] = profile.getPreferenceColour('model_colour')
		if self._switchColors:
			self._objColors.reverse()
			self._extrudersColors.reverse()
		self._scene.updateMachineDimensions()
		self.updateModelSettingsToControls()

	def updateModelSettingsToControls(self):
		if self._selectedObj is not None:
			scale = self._selectedObj.getScale()
			size = self._selectedObj.getSize()
			self.scaleXctrl.setValue(round(scale[0], 2))
			self.scaleYctrl.setValue(round(scale[1], 2))
			self.scaleZctrl.setValue(round(scale[2], 2))
			self.scaleXmmctrl.setValue(round(size[0], 2))
			self.scaleYmmctrl.setValue(round(size[1], 2))
			self.scaleZmmctrl.setValue(round(size[2], 2))

	def OnKeyChar(self, keyCode):
		if self._engineResultView.OnKeyChar(keyCode):
			return
		if keyCode == wx.WXK_DELETE or keyCode == wx.WXK_NUMPAD_DELETE or (keyCode == wx.WXK_BACK and sys.platform.startswith("darwin")):
			if self._selectedObj is not None:
				self._deleteObject(self._selectedObj)
				self.QueueRefresh()
		if keyCode == wx.WXK_UP:
			if wx.GetKeyState(wx.WXK_SHIFT):
				self._zoom /= 1.2
				if self._zoom < 1:
					self._zoom = 1
			else:
				self._pitch -= 15
			self.QueueRefresh()
		elif keyCode == wx.WXK_DOWN:
			if wx.GetKeyState(wx.WXK_SHIFT):
				self._zoom *= 1.2
				if self._zoom > numpy.max(self._machineSize) * 3:
					self._zoom = numpy.max(self._machineSize) * 3
			else:
				self._pitch += 15
			self.QueueRefresh()
		elif keyCode == wx.WXK_LEFT:
			self._yaw -= 15
			self.QueueRefresh()
		elif keyCode == wx.WXK_RIGHT:
			self._yaw += 15
			self.QueueRefresh()
		elif keyCode == wx.WXK_NUMPAD_ADD or keyCode == wx.WXK_ADD or keyCode == ord('+') or keyCode == ord('='):
			self._zoom /= 1.2
			if self._zoom < 1:
				self._zoom = 1
			self.QueueRefresh()
		elif keyCode == wx.WXK_NUMPAD_SUBTRACT or keyCode == wx.WXK_SUBTRACT or keyCode == ord('-'):
			self._zoom *= 1.2
			if self._zoom > numpy.max(self._machineSize) * 3:
				self._zoom = numpy.max(self._machineSize) * 3
			self.QueueRefresh()
		elif keyCode == wx.WXK_HOME:
			self._yaw = 30
			self._pitch = 60
			self.QueueRefresh()
		elif keyCode == wx.WXK_PAGEUP:
			self._yaw = 0
			self._pitch = 0
			self.QueueRefresh()
		elif keyCode == wx.WXK_PAGEDOWN:
			self._yaw = 0
			self._pitch = 90
			self.QueueRefresh()
		elif keyCode == wx.WXK_END:
			self._yaw = 90
			self._pitch = 90
			self.QueueRefresh()

		if keyCode == wx.WXK_F3 and wx.GetKeyState(wx.WXK_SHIFT):
			shaderEditor(self, self.ShaderUpdate, self._objectLoadShader.getVertexShader(), self._objectLoadShader.getFragmentShader())
		if keyCode == wx.WXK_F4 and wx.GetKeyState(wx.WXK_SHIFT):
			from collections import defaultdict
			from gc import get_objects
			self._beforeLeakTest = defaultdict(int)
			for i in get_objects():
				self._beforeLeakTest[type(i)] += 1
		if keyCode == wx.WXK_F5 and wx.GetKeyState(wx.WXK_SHIFT):
			from collections import defaultdict
			from gc import get_objects
			self._afterLeakTest = defaultdict(int)
			for i in get_objects():
				self._afterLeakTest[type(i)] += 1
			for k in self._afterLeakTest:
				if self._afterLeakTest[k]-self._beforeLeakTest[k]:
					print(k, self._afterLeakTest[k], self._beforeLeakTest[k], self._afterLeakTest[k] - self._beforeLeakTest[k])

	def ShaderUpdate(self, v, f):
		s = openglHelpers.GLShader(v, f)
		if s.isValid():
			self._objectLoadShader.release()
			self._objectLoadShader = s
			for obj in self._scene.objects():
				obj._loadAnim = openglGui.animation(self, 1, 0, 1.5)
			self.QueueRefresh()

	def OnMouseDown(self,e):
		self._mouseX = e.GetX() * self.GetContentScaleFactor()
		self._mouseY = e.GetY() * self.GetContentScaleFactor()
		self._mouseClick3DPos = self._mouse3Dpos
		self._mouseClickFocus = self._focusObj
		if e.ButtonDClick():
			self._mouseState = 'doubleClick'
		else:
			if self._mouseState == 'dragObject' and self._selectedObj is not None:
				self._scene.pushFree(self._selectedObj)
				self.sceneUpdated()
			self._mouseState = 'dragOrClick'
		p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
		p0 -= self.getObjectCenterPos() - self._viewTarget
		p1 -= self.getObjectCenterPos() - self._viewTarget
		if self.tool.OnDragStart(p0, p1):
			self._mouseState = 'tool'
		if self._mouseState == 'dragOrClick':
			if e.GetButton() == 1:
				if self._focusObj is not None:
					self._selectObject(self._focusObj, False)
					self.QueueRefresh()

	def OnMouseUp(self, e):
		if e.LeftIsDown() or e.MiddleIsDown() or e.RightIsDown():
			return
		if self._mouseState == 'dragOrClick':
			if e.GetButton() == 1:
				self._selectObject(self._focusObj)
			if e.GetButton() == 3:
				menu = wx.Menu()
				if self._focusObj is not None:
					self.Bind(wx.EVT_MENU, self.OnCenter, menu.Append(-1, _("Center on platform")))
					self.Bind(wx.EVT_MENU, lambda e: self._deleteObject(self._focusObj), menu.Append(-1, _("Delete object")))
					self.Bind(wx.EVT_MENU, self.OnMultiply, menu.Append(-1, _("Multiply object")))
					self.Bind(wx.EVT_MENU, self.OnSplitObject, menu.Append(-1, _("Split object into parts")))
				if ((self._selectedObj != self._focusObj and self._focusObj is not None and self._selectedObj is not None) or len(self._scene.objects()) == 2) and int(profile.getMachineSetting('extruder_amount')) > 1:
					self.Bind(wx.EVT_MENU, self.OnMergeObjects, menu.Append(-1, _("Dual extrusion merge")))
				if (self._focusObj is not None or self._selectedObj is not None) and profile.mergeDone and int(profile.getMachineSetting('extruder_amount')) == 2:
					self.Bind(wx.EVT_MENU, self.OnSwitchColors, menu.Append(-1, _("Switch colors")))
				if len(self._scene.objects()) > 0:
					self.Bind(wx.EVT_MENU, self.OnDeleteAll, menu.Append(-1, _("Delete all objects")))
					self.Bind(wx.EVT_MENU, self.reloadScene, menu.Append(-1, _("Reload all objects")))
				if menu.MenuItemCount > 0:
					self.PopupMenu(menu)
				menu.Destroy()
		elif self._mouseState == 'dragObject' and self._selectedObj is not None:
			self._scene.pushFree(self._selectedObj)
			self.sceneUpdated()
		elif self._mouseState == 'tool':
			if self.tempMatrix is not None and self._selectedObj is not None:
				self._selectedObj.applyMatrix(self.tempMatrix)
				self._scene.pushFree(self._selectedObj)
				self._selectObject(self._selectedObj)
			self.tempMatrix = None
			self.tool.OnDragEnd()
			self.sceneUpdated()
		self._mouseState = None

	def OnMouseMotion(self,e):
		p0, p1 = self.getMouseRay(e.GetX() * self.GetContentScaleFactor(), e.GetY() * self.GetContentScaleFactor())
		p0 -= self.getObjectCenterPos() - self._viewTarget
		p1 -= self.getObjectCenterPos() - self._viewTarget

		if e.Dragging() and self._mouseState is not None:
			if self._mouseState == 'tool':
				self.tool.OnDrag(p0, p1)
			elif not e.LeftIsDown() and e.RightIsDown():
				self._mouseState = 'drag'
				if wx.GetKeyState(wx.WXK_SHIFT):
					a = math.cos(math.radians(self._yaw)) / 3.0
					b = math.sin(math.radians(self._yaw)) / 3.0
					self._viewTarget[0] += float(e.GetX() * self.GetContentScaleFactor() - self._mouseX) * -a
					self._viewTarget[1] += float(e.GetX() * self.GetContentScaleFactor() - self._mouseX) * b
					self._viewTarget[0] += float(e.GetY() * self.GetContentScaleFactor() - self._mouseY) * b
					self._viewTarget[1] += float(e.GetY() * self.GetContentScaleFactor() - self._mouseY) * a
				else:
					self._yaw += (e.GetX() * self.GetContentScaleFactor()) - self._mouseX
					self._pitch -= (e.GetY() * self.GetContentScaleFactor()) - self._mouseY
				if self._pitch > 170:
					self._pitch = 170
				if self._pitch < 10:
					self._pitch = 10
			elif (e.LeftIsDown() and e.RightIsDown()) or e.MiddleIsDown():
				self._mouseState = 'drag'
				self._zoom += e.GetY() - self._mouseY
				if self._zoom < 1:
					self._zoom = 1
				if self._zoom > numpy.max(self._machineSize) * 3:
					self._zoom = numpy.max(self._machineSize) * 3
			elif e.LeftIsDown() and self._selectedObj is not None and self._selectedObj == self._mouseClickFocus:
				self._mouseState = 'dragObject'
				z = max(0, self._mouseClick3DPos[2])
				p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
				p2, p3 = self.getMouseRay(e.GetX() * self.GetContentScaleFactor(), e.GetY() * self.GetContentScaleFactor())
				p0[2] -= z
				p1[2] -= z
				p2[2] -= z
				p3[2] -= z
				cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2]))
				cursorZ1 = p2 - (p3 - p2) * (p2[2] / (p3[2] - p2[2]))
				diff = cursorZ1 - cursorZ0
				self._selectedObj.setPosition(self._selectedObj.getPosition() + diff[0:2])
		if not e.Dragging() or self._mouseState != 'tool':
			self.tool.OnMouseMove(p0, p1)

		self._mouseX = e.GetX() * self.GetContentScaleFactor()
		self._mouseY = e.GetY() * self.GetContentScaleFactor()

	def OnMouseWheel(self, e):
		delta = float(e.GetWheelRotation()) / float(e.GetWheelDelta())
		delta = max(min(delta,4),-4)
		self._zoom *= 1.0 - delta / 10.0
		if self._zoom < 1.0:
			self._zoom = 1.0
		if self._zoom > numpy.max(self._machineSize) * 3:
			self._zoom = numpy.max(self._machineSize) * 3
		self.Refresh()

	def OnMouseLeave(self, e):
		#self._mouseX = -1
		pass

	def getMouseRay(self, x, y):
		if self._viewport is None:
			return numpy.array([0,0,0],numpy.float32), numpy.array([0,0,1],numpy.float32)
		p0 = openglHelpers.unproject(x, self._viewport[1] + self._viewport[3] - y, 0, self._modelMatrix, self._projMatrix, self._viewport)
		p1 = openglHelpers.unproject(x, self._viewport[1] + self._viewport[3] - y, 1, self._modelMatrix, self._projMatrix, self._viewport)
		p0 -= self._viewTarget
		p1 -= self._viewTarget
		return p0, p1

	def _init3DView(self):
		# set viewing projection
		size = self.GetSize() * self.GetContentScaleFactor()
		glViewport(0, 0, size.GetWidth(), size.GetHeight())
		glLoadIdentity()

		glLightfv(GL_LIGHT0, GL_POSITION, [0.2, 0.2, 1.0, 0.0])

		glDisable(GL_RESCALE_NORMAL)
		glDisable(GL_LIGHTING)
		glDisable(GL_LIGHT0)
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_CULL_FACE)
		glDisable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		glClearColor(0.8, 0.8, 0.8, 1.0)
		glClearStencil(0)
		glClearDepth(1.0)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		aspect = float(size.GetWidth()) / float(size.GetHeight())
		gluPerspective(45.0, aspect, 1.0, numpy.max(self._machineSize) * 4)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

	def OnPaint(self,e):
		self.printButton._imageID = None
		self.printButton._tooltip = _(" ")

		if self._animView is not None:
			self._viewTarget = self._animView.getPosition()
			if self._animView.isDone():
				self._animView = None
		if self._animZoom is not None:
			self._zoom = self._animZoom.getPosition()
			if self._animZoom.isDone():
				self._animZoom = None
		if self._objectShader is None: #TODO: add loading shaders from file(s)
			if openglHelpers.hasShaderSupport():
				self._objectShader = openglHelpers.GLShader("""
					varying float light_amount;

					void main(void)
					{
						gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
						gl_FrontColor = gl_Color;

						light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
						light_amount += 0.2;
					}
									""","""
					varying float light_amount;

					void main(void)
					{
						gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
					}
				""")
				self._objectOverhangShader = openglHelpers.GLShader("""
					uniform float cosAngle;
					uniform mat3 rotMatrix;
					varying float light_amount;

					void main(void)
					{
						gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
						gl_FrontColor = gl_Color;

						light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
						light_amount += 0.2;
						if (normalize(rotMatrix * gl_Normal).z < -cosAngle)
						{
							light_amount = -10.0;
						}
					}
				""","""
					varying float light_amount;

					void main(void)
					{
						if (light_amount == -10.0)
						{
							gl_FragColor = vec4(1.0, 0.0, 0.0, gl_Color[3]);
						}else{
							gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
						}
					}
									""")
				self._objectLoadShader = openglHelpers.GLShader("""
					uniform float intensity;
					uniform float scale;
					varying float light_amount;

					void main(void)
					{
						vec4 tmp = gl_Vertex;
						tmp.x += sin(tmp.z/5.0+intensity*30.0) * scale * intensity;
						tmp.y += sin(tmp.z/3.0+intensity*40.0) * scale * intensity;
						gl_Position = gl_ModelViewProjectionMatrix * tmp;
						gl_FrontColor = gl_Color;

						light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
						light_amount += 0.2;
					}
			""","""
				uniform float intensity;
				varying float light_amount;

				void main(void)
				{
					gl_FragColor = vec4(gl_Color.xyz * light_amount, 1.0-intensity);
				}
				""")
			if self._objectShader is None or not self._objectShader.isValid(): #Could not make shader.
				self._objectShader = openglHelpers.GLFakeShader()
				self._objectOverhangShader = openglHelpers.GLFakeShader()
				self._objectLoadShader = None
		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		self._viewport = glGetIntegerv(GL_VIEWPORT)
		self._modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self._projMatrix = glGetDoublev(GL_PROJECTION_MATRIX)

		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		if self.viewMode != 'gcode':
			for n in range(0, len(self._scene.objects())):
				obj = self._scene.objects()[n]
				glColor4ub((n >> 16) & 0xFF, (n >> 8) & 0xFF, (n >> 0) & 0xFF, 0xFF)
				self._renderObject(obj)

		if self._mouseX > -1: # mouse has not passed over the opengl window.
			glFlush()
			n = glReadPixels(self._mouseX, (self.GetSize() * self.GetContentScaleFactor()).GetHeight() - 1 - self._mouseY, 1, 1, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8
			if n < len(self._scene.objects()):
				self._focusObj = self._scene.objects()[n]
			else:
				self._focusObj = None
			f = glReadPixels(self._mouseX, (self.GetSize() * self.GetContentScaleFactor()).GetHeight() - 1 - self._mouseY, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]
			#self.GetTopLevelParent().SetTitle(hex(n) + " " + str(f))
			self._mouse3Dpos = openglHelpers.unproject(self._mouseX, self._viewport[1] + self._viewport[3] - self._mouseY, f, self._modelMatrix, self._projMatrix, self._viewport)
			self._mouse3Dpos -= self._viewTarget

		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		self._objectShader.unbind()
		self._engineResultView.OnDraw()
		if self.viewMode != 'gcode':
			glStencilFunc(GL_ALWAYS, 1, 1)
			glStencilOp(GL_INCR, GL_INCR, GL_INCR)

			if self.viewMode == 'overhang':
				self._objectOverhangShader.bind()
				self._objectOverhangShader.setUniform('cosAngle', math.cos(math.radians(90 - profile.getProfileSettingFloat('support_angle'))))
			else:
				self._objectShader.bind()
			for obj in self._scene.objects():
				if obj._loadAnim is not None:
					if obj._loadAnim.isDone():
						obj._loadAnim = None
					else:
						continue
				brightness = 1.0
				if self._focusObj == obj:
					brightness = 1.2
				elif self._focusObj is not None or self._selectedObj is not None and obj != self._selectedObj:
					brightness = 0.8

				if self._selectedObj == obj or self._selectedObj is None:
					#If we want transparent, then first render a solid black model to remove the printer size lines.
					if self.viewMode == 'transparent':
						glColor4f(0, 0, 0, 0)
						self._renderObject(obj)
						glEnable(GL_BLEND)
						glBlendFunc(GL_ONE, GL_ONE)
						glDisable(GL_DEPTH_TEST)
						brightness *= 0.5
					if self.viewMode == 'xray':
						glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
					glStencilOp(GL_INCR, GL_INCR, GL_INCR)
					glEnable(GL_STENCIL_TEST)

				if self.viewMode == 'overhang':
					if self._selectedObj == obj and self.tempMatrix is not None:
						self._objectOverhangShader.setUniform('rotMatrix', obj.getMatrix() * self.tempMatrix)
					else:
						self._objectOverhangShader.setUniform('rotMatrix', obj.getMatrix())

				if not self._scene.checkPlatform(obj):
					glColor4f(0.5 * brightness, 0.5 * brightness, 0.5 * brightness, 0.8 * brightness)
					self._renderObject(obj)
				else:
					self._renderObject(obj, brightness)
				glDisable(GL_STENCIL_TEST)
				glDisable(GL_BLEND)
				glEnable(GL_DEPTH_TEST)
				glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

			if self.viewMode == 'xray':
				glPushMatrix()
				glLoadIdentity()
				glEnable(GL_STENCIL_TEST)
				glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP) #Keep values
				glDisable(GL_DEPTH_TEST)
				for i in range(2, 15, 2): #All even values
					glStencilFunc(GL_EQUAL, i, 0xFF)
					glColor(float(i)/10, float(i)/10, float(i)/5)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-10)
					glVertex3f( 1000,-1000,-10)
					glVertex3f( 1000, 1000,-10)
					glVertex3f(-1000, 1000,-10)
					glEnd()
				for i in range(1, 15, 2): #All odd values
					glStencilFunc(GL_EQUAL, i, 0xFF)
					glColor(float(i)/10, 0, 0)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-10)
					glVertex3f( 1000,-1000,-10)
					glVertex3f( 1000, 1000,-10)
					glVertex3f(-1000, 1000,-10)
					glEnd()
				glPopMatrix()
				glDisable(GL_STENCIL_TEST)
				glEnable(GL_DEPTH_TEST)

			self._objectShader.unbind()

			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
			glEnable(GL_BLEND)
			if self._objectLoadShader is not None:
				self._objectLoadShader.bind()
				glColor4f(0.2, 0.6, 1.0, 1.0)
				for obj in self._scene.objects():
					if obj._loadAnim is None:
						continue
					self._objectLoadShader.setUniform('intensity', obj._loadAnim.getPosition())
					self._objectLoadShader.setUniform('scale', obj.getBoundaryCircle() / 10)
					self._renderObject(obj)
				self._objectLoadShader.unbind()
				glDisable(GL_BLEND)

		self._drawMachine()

		if self.viewMode != 'gcode':
			#Draw the object box-shadow, so you can see where it will collide with other objects.
			if self._selectedObj is not None:
				glEnable(GL_BLEND)
				glEnable(GL_CULL_FACE)
				glColor4f(0,0,0,0.16)
				glDepthMask(False)
				for obj in self._scene.objects():
					glPushMatrix()
					glTranslatef(obj.getPosition()[0], obj.getPosition()[1], 0)
					glBegin(GL_TRIANGLE_FAN)
					for p in obj._boundaryHull[::-1]:
						glVertex3f(p[0], p[1], 0)
					glEnd()
					glPopMatrix()
				if self._scene.isOneAtATime(): #Check print sequence mode.
					glPushMatrix()
					glColor4f(0,0,0,0.06)
					glTranslatef(self._selectedObj.getPosition()[0], self._selectedObj.getPosition()[1], 0)
					glBegin(GL_TRIANGLE_FAN)
					for p in self._selectedObj._printAreaHull[::-1]:
						glVertex3f(p[0], p[1], 0)
					glEnd()
					glBegin(GL_TRIANGLE_FAN)
					for p in self._selectedObj._headAreaMinHull[::-1]:
						glVertex3f(p[0], p[1], 0)
					glEnd()
					glPopMatrix()
				glDepthMask(True)
				glDisable(GL_CULL_FACE)

			#Draw the outline of the selected object on top of everything else except the GUI.
			if self._selectedObj is not None and self._selectedObj._loadAnim is None:
				glDisable(GL_DEPTH_TEST)
				glEnable(GL_CULL_FACE)
				glEnable(GL_STENCIL_TEST)
				glDisable(GL_BLEND)
				glStencilFunc(GL_EQUAL, 0, 255)

				glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
				glLineWidth(2)
				glColor4f(1,1,1,0.5)
				self._renderObject(self._selectedObj)
				glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

				size = self.GetSize() * self.GetContentScaleFactor()
				glViewport(0, 0, size.GetWidth(), size.GetHeight())
				glDisable(GL_STENCIL_TEST)
				glDisable(GL_CULL_FACE)
				glEnable(GL_DEPTH_TEST)

			if self._selectedObj is not None:
				glPushMatrix()
				pos = self.getObjectCenterPos()
				glTranslate(pos[0], pos[1], pos[2])
				self.tool.OnDraw()
				glPopMatrix()
		if self.viewMode == 'overhang' and not openglHelpers.hasShaderSupport():
			glDisable(GL_DEPTH_TEST)
			glPushMatrix()
			glLoadIdentity()
			glTranslate(0,-4,-10)
			glColor4ub(60,60,60,255)
			openglHelpers.glDrawStringCenter(_("Overhang view not working due to lack of OpenGL shaders support."))
			glPopMatrix()

	def _renderObject(self, obj, brightness = 0, addSink = True):
		glPushMatrix()
		if addSink:
			glTranslate(obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2 - profile.getProfileSettingFloat('object_sink'))
		else:
			glTranslate(obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2)

		if self.tempMatrix is not None and obj == self._selectedObj:
			glMultMatrixf(openglHelpers.convert3x3MatrixTo4x4(self.tempMatrix))

		offset = obj.getDrawOffset()
		glTranslate(-offset[0], -offset[1], -offset[2] - obj.getSize()[2] / 2)

		glMultMatrixf(openglHelpers.convert3x3MatrixTo4x4(obj.getMatrix()))

		n = 0
		for m in obj._meshList:
			if m.vbo is None:
				m.vbo = openglHelpers.GLVBO(GL_TRIANGLES, m.vertexes, m.normal)
			if brightness != 0:
				glColor4fv([idx * brightness for idx in self._objColors[n]])
				n = (n + 1) % len(self._objColors)
			m.vbo.render()
		glPopMatrix()

	def _drawMachine(self):
		glEnable(GL_CULL_FACE)
		glEnable(GL_BLEND)

		size = [profile.getMachineSettingFloat('machine_width'), profile.getMachineSettingFloat('machine_depth'), profile.getMachineSettingFloat('machine_height')]

		machine = profile.getMachineSetting('machine_name')
		if int(profile.getMachineSetting('extruder_amount')) == 2:
			machine += '_dual'
		if machine.startswith('DiscoUltimate') or machine.startswith('DiscoEasy200') or machine.startswith('DiscoVery200') or machine.startswith('Neva') or machine.startswith('Magis') or machine.startswith('Explorer350') or machine.startswith('Sigma'):
			if machine not in self._platformMesh:
				meshes = meshLoader.loadMeshes(resources.getPathForMesh(machine.lower() + '.stl'))
				if len(meshes) > 0:
					self._platformMesh[machine] = meshes[0]
				else:
					self._platformMesh[machine] = None

				if machine in ['DiscoEasy200', 'DiscoUltimate']:
					self._platformMesh[machine]._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
					self._platformMesh[machine].processMatrix()
					#print 'self._platformMesh[machine]._matrix', self._platformMesh[machine]._matrix
					if machine == 'DiscoEasy200':
						self._platformMesh[machine]._drawOffset = numpy.array([-105,285,58], numpy.float32)
					elif machine == 'DiscoUltimate':
						self._platformMesh[machine]._drawOffset = numpy.array([-105,285,62], numpy.float32)
				elif machine in ['DiscoEasy200_dual', 'DiscoUltimate_dual']:
					if int(profile.getMachineSetting('extruder_amount')) == 2:
						self._platformMesh[machine]._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
						self._platformMesh[machine].processMatrix()
						#print 'self._platformMesh[machine]._matrix', self._platformMesh[machine]._matrix
						if machine == 'DiscoEasy200_dual':
							self._platformMesh[machine]._drawOffset = numpy.array([-105,285,58], numpy.float32)
						elif machine == 'DiscoUltimate_dual':
							self._platformMesh[machine]._drawOffset = numpy.array([-105,285,62], numpy.float32)

						meshes = meshLoader.loadMeshes(resources.getPathForMesh(machine.lower() + '_t0.stl'))
						self._platformMesh[machine + '_t0'] = meshes[0]
						self._platformMesh[machine + '_t0']._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
						self._platformMesh[machine + '_t0'].processMatrix()
						#print 'self._platformMesh[machine + '_bed']._matrix', self._platformMesh[machine]._matrix
						if machine == 'DiscoEasy200_dual':
							self._platformMesh[machine + '_t0']._drawOffset = numpy.array([-105,285,58], numpy.float32)
						elif machine == 'DiscoUltimate_dual':
							self._platformMesh[machine + '_t0']._drawOffset = numpy.array([-105,285,62], numpy.float32)

						meshes = meshLoader.loadMeshes(resources.getPathForMesh(machine.lower() + '_t1.stl'))
						self._platformMesh[machine + '_t1'] = meshes[0]
						self._platformMesh[machine + '_t1']._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
						self._platformMesh[machine + '_t1'].processMatrix()
						#print 'self._platformMesh[machine + '_bed']._matrix', self._platformMesh[machine]._matrix
						if machine == 'DiscoEasy200_dual':
							self._platformMesh[machine + '_t1']._drawOffset = numpy.array([-105,285,58], numpy.float32)
						elif machine == 'DiscoUltimate_dual':
							self._platformMesh[machine + '_t1']._drawOffset = numpy.array([-105,285,62], numpy.float32)
				elif machine == 'DiscoVery200':
					self._platformMesh[machine]._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
					self._platformMesh[machine].processMatrix()
					#print 'self._platformMesh[machine]._matrix', self._platformMesh[machine]._matrix
					self._platformMesh[machine]._drawOffset = numpy.array([17.5,272,52], numpy.float32)
				elif machine == 'Neva':
					self._platformMesh[machine]._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
					self._platformMesh[machine].processMatrix()
					#print 'self._platformMesh[machine]._matrix', self._platformMesh[machine]._matrix
					self._platformMesh[machine]._drawOffset = numpy.array([-153,103,53], numpy.float32)
				elif machine in ['Magis', 'Sigma']:
					self._platformMesh[machine]._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
					self._platformMesh[machine].processMatrix()
					#print 'self._platformMesh[machine]._matrix', self._platformMesh[machine]._matrix
					self._platformMesh[machine]._drawOffset = numpy.array([-153.02630615,103.5,643], numpy.float32)
					#print self._platformMesh[machine]._drawOffset
				elif machine == 'Explorer350':
					self._platformMesh[machine]._matrix = numpy.matrix([[-1,-1.23259516e-32,-1.22464680e-16],[-1.22464680e-16,1.38777878e-16,1],[0,1,-1.38777878e-16]], numpy.float64)
					self._platformMesh[machine].processMatrix()
					#print 'self._platformMesh[machine]._matrix', self._platformMesh[machine]._matrix
					self._platformMesh[machine]._drawOffset = numpy.array([-301,381,117], numpy.float32)#303,383,117;306 386 115 (X, Y, Z ) #X inverse : -100 va vers la droite, +Y vers le devant, Z+ vers le bas
				else:
					self._platformMesh[machine]._drawOffset = numpy.array([0,0,2.5], numpy.float32)
			glColor4f(1,1,1,0.5)
			self._objectShader.bind()
			self._renderObject(self._platformMesh[machine], False, False)
			if int(profile.getMachineSetting('extruder_amount')) == 2:
				glColor4f(self._extrudersColors[0][0], self._extrudersColors[0][1], self._extrudersColors[0][2], 0.5)
				self._renderObject(self._platformMesh[machine + '_t0'], False, False)
				glColor4f(self._extrudersColors[1][0], self._extrudersColors[1][1], self._extrudersColors[1][2], 0.5)
				self._renderObject(self._platformMesh[machine + '_t1'], False, False)
			self._objectShader.unbind()
		else:
			glColor4f(0,0,0,1)
			glLineWidth(3)
			glBegin(GL_LINES)
			glVertex3f(-size[0] / 2, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2, -size[1] / 2, 10)
			glVertex3f(-size[0] / 2, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2+10, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2, -size[1] / 2+10, 0)
			glEnd()

		glDepthMask(False)

		polys = profile.getMachineSizePolygons()
		height = profile.getMachineSettingFloat('machine_height')
		circular = profile.getMachineSetting('machine_shape') == 'Circular'
		glBegin(GL_QUADS)
		# Draw the sides of the build volume.
		for n in range(0, len(polys[0])):
			if not circular:
				if n % 2 == 0:
					glColor4ub(5, 171, 231, 96)
				else:
					glColor4ub(5, 171, 231, 64)
			else:
				glColor4ub(5, 171, 231, 96)

			glVertex3f(polys[0][n][0], polys[0][n][1], height)
			glVertex3f(polys[0][n][0], polys[0][n][1], 0)
			glVertex3f(polys[0][n-1][0], polys[0][n-1][1], 0)
			glVertex3f(polys[0][n-1][0], polys[0][n-1][1], height)
		glEnd()

		#Draw top of build volume.
		glColor4ub(5, 171, 231, 128)
		glBegin(GL_TRIANGLE_FAN)
		for p in polys[0][::-1]:
			glVertex3f(p[0], p[1], height)
		glEnd()

		#Draw checkerboard
		if self._platformTexture is None:
			self._platformTexture = openglHelpers.loadGLTexture('checkerboard.png')
			glBindTexture(GL_TEXTURE_2D, self._platformTexture)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glColor4f(1,1,1,0.5)
		glBindTexture(GL_TEXTURE_2D, self._platformTexture)
		glEnable(GL_TEXTURE_2D)
		glBegin(GL_TRIANGLE_FAN)
		for p in polys[0]:
			glTexCoord2f(p[0]/20, p[1]/20)
			glVertex3f(p[0], p[1], 0)
		glEnd()

		#Draw no-go zones. (clips in case of UM2)
		glDisable(GL_TEXTURE_2D)
		glColor4ub(127, 127, 127, 200)
		for poly in polys[1:]:
			glBegin(GL_TRIANGLE_FAN)
			for p in poly:
				glTexCoord2f(p[0]/20, p[1]/20)
				glVertex3f(p[0], p[1], 0)
			glEnd()

		glDepthMask(True)
		glDisable(GL_BLEND)
		glDisable(GL_CULL_FACE)

	def getObjectCenterPos(self):
		if self._selectedObj is None:
			return [0.0, 0.0, 0.0]
		pos = self._selectedObj.getPosition()
		size = self._selectedObj.getSize()
		return [pos[0], pos[1], size[2]/2 - profile.getProfileSettingFloat('object_sink')]

	def getObjectBoundaryCircle(self):
		if self._selectedObj is None:
			return 0.0
		return self._selectedObj.getBoundaryCircle()

	def getObjectSize(self):
		if self._selectedObj is None:
			return [0.0, 0.0, 0.0]
		return self._selectedObj.getSize()

	def getObjectMatrix(self):
		if self._selectedObj is None:
			return numpy.matrix(numpy.identity(3))
		return self._selectedObj.getMatrix()

#TODO: Remove this or put it in a seperate file
class shaderEditor(wx.Frame):
	def __init__(self, parent, callback, v, f):
		super(shaderEditor, self).__init__(parent, title="Shader editor", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self._callback = callback
		s = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(s)
		self._vertex = wx.TextCtrl(self, -1, v, style=wx.TE_MULTILINE)
		self._fragment = wx.TextCtrl(self, -1, f, style=wx.TE_MULTILINE)
		s.Add(self._vertex, 1, flag=wx.EXPAND)
		s.Add(self._fragment, 1, flag=wx.EXPAND)

		self._vertex.Bind(wx.EVT_TEXT, self.OnText, self._vertex)
		self._fragment.Bind(wx.EVT_TEXT, self.OnText, self._fragment)

		self.SetPosition(self.GetParent().GetPosition())
		self.SetSize((self.GetSize().GetWidth(), self.GetParent().GetSize().GetHeight()))
		self.Show()

	def OnText(self, e):
		self._callback(self._vertex.GetValue(), self._fragment.GetValue())
