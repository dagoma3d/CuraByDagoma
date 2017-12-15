__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import os
import webbrowser
from wx.lib import scrolledpanel

from Cura.util import profile
from Cura.util import pluginInfo
from Cura.util import explorer

class pausePluginPanel(wx.Panel):
	def __init__(self, parent, callback):
		wx.Panel.__init__(self, parent, -1)
		#Plugin page
		self.plugin = pluginInfo.getPlugin("postprocess", 'pauseAtZ-ByDagoma.py')
		self.callback = callback
		pluginInfo.setPostProcessPluginConfig()

		sizer = wx.GridBagSizer(1, 1)
		self.SetSizer(sizer)

		lPauseTitle = wx.StaticText(self, -1, _("Add a pause")) # (92, 27) is the default size of a TextCtrl and (80, 17) is the default size of a StaticText
		addLayerButton = wx.Button(self, id=-1, label="+", style=wx.BU_EXACTFIT)
		lPauseTitleToolTip = wx.ToolTip(_("Add a pause at the layer selected in the 3D view"))
		addLayerButton.SetToolTip(lPauseTitleToolTip)
		sb = wx.StaticBox(self)

		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.SetMinSize(wx.Size(0, 170))
		self.pluginEnabledPanel = scrolledpanel.ScrolledPanel(self)
		self.pluginEnabledPanel.SetupScrolling(False, True)

		sizer.Add(boxsizer, pos=(0,0), span=(1,1), flag=wx.EXPAND)

		mysizer = wx.GridBagSizer(2, 4)
		mysizer.Add(lPauseTitle, pos=(0,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		mysizer.Add(addLayerButton, pos=(0,2), span=(1,2), flag=wx.ALIGN_LEFT)
		#mysizer.Add(hPauseTitle, pos=(0,2), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		#mysizer.Add(addHeightButton, pos=(0,3), span=(1,1), flag=wx.ALIGN_LEFT)
		mysizer.Add(wx.StaticLine(self), pos=(1,0), span=(1,4), flag=wx.EXPAND|wx.ALL, border=3)
		mysizer.AddGrowableCol(0)
		mysizer.AddGrowableCol(1)
		mysizer.AddGrowableCol(2)
		mysizer.AddGrowableCol(3)

		boxsizer.Add(mysizer, 0, flag=wx.EXPAND)
		boxsizer.Add(self.pluginEnabledPanel, 1, flag=wx.EXPAND)

		self.boxsizer = boxsizer

		sizer.AddGrowableCol(0)
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.pluginEnabledPanel.SetSizer(sizer)

		#self.Bind(wx.EVT_BUTTON, self.OnAddHeight, addHeightButton)
		self.Bind(wx.EVT_BUTTON, self.OnAddLayer, addLayerButton)
		self.panelList = []
		self.updateProfileToControls()

	def updateProfileToControls(self):
		self.pluginConfig = pluginInfo.getPostProcessPluginConfig()
		for p in self.panelList:
			p.Show(False)
			self.pluginEnabledPanel.GetSizer().Detach(p)
		self.panelList = []
		for pluginConfig in self.pluginConfig:
			self._buildPluginPanel(pluginConfig)

	def _buildPluginPanel(self, pluginConfig):
		pausePluginPanel = wx.Panel(self.pluginEnabledPanel)
		s = wx.GridBagSizer(1, 4)
		pausePluginPanel.SetSizer(s)
		pausePluginPanel.paramCtrls = {}
		scene = self.GetParent().GetParent().GetParent().GetParent().scene

		remButton1 = wx.Button(pausePluginPanel, id=-1, label="x", style=wx.BU_EXACTFIT)
		s.Add(remButton1, pos=(0,0), span=(1,1), flag=wx.ALIGN_LEFT)

		i = 1
		for param in self.plugin.getParams():
			#value = param['default']
			value = ''
			if param['name'] in pluginConfig['params']:
				value = pluginConfig['params'][param['name']]

			ctrl = wx.TextCtrl(pausePluginPanel, -1, value)
			height_value = float(value) * float(profile.getProfileSettingFloat('layer_height'))
			height_label = wx.TextCtrl(pausePluginPanel, -1, str(height_value) + ' mm')
			height_label.Disable()
			if value == '':
				ctrl.Disable()
			s.Add(ctrl, pos=(0,i), span=(1,1), flag=wx.EXPAND)
			s.Add(height_label, pos=(0,i+1), span=(1,1), flag=wx.EXPAND)
			ctrl.Bind(wx.EVT_TEXT, self.OnSettingChange)

			pausePluginPanel.paramCtrls[param['name']] = ctrl

			i += 1
		remButton2 = wx.Button(pausePluginPanel, id=-1, label="x", style=wx.BU_EXACTFIT)
		s.Add(remButton2, pos=(0,i+1), span=(1,1), flag=wx.ALIGN_LEFT)

		s.AddGrowableCol(1)
		s.AddGrowableCol(2)

		self.Bind(wx.EVT_BUTTON, self.OnRem, remButton1)
		self.Bind(wx.EVT_BUTTON, self.OnRem, remButton2)

		pausePluginPanel.SetBackgroundColour(self.GetParent().GetBackgroundColour())
		pausePluginPanel.Layout()
		self.pluginEnabledPanel.GetSizer().Add(pausePluginPanel, flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.pluginEnabledPanel.Layout()
		self.pluginEnabledPanel.SetSize((1,1))
		self.Layout()
		self.pluginEnabledPanel.ScrollChildIntoView(pausePluginPanel)
		self.panelList.append(pausePluginPanel)
		return True

	def OnSettingChange(self, e):
		changed_panel = e.GetEventObject().GetParent()
		panelChildren = changed_panel.GetSizer().GetChildren()
		for panelChild in panelChildren:
			panelWidget = panelChild.GetWindow()
			# The only disabled textctrl by line is the one containing the height info
			if isinstance(panelWidget, wx.TextCtrl) and not panelWidget.IsEnabled():
				height_value = float(e.GetEventObject().GetValue()) * float(profile.getProfileSettingFloat('layer_height'))
				if(e.IsCommandEvent()):
					panelWidget.SetValue(str(height_value) + ' mm')
		for panel in self.panelList:
			idx = self.panelList.index(panel)
			for k in panel.paramCtrls.keys():
				self.pluginConfig[idx]['params'][k] = panel.paramCtrls[k].GetValue()
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()

	def OnAddHeight(self, e):
		scene = self.GetParent().GetParent().GetParent().GetParent().scene
		if scene.viewMode == 'normal':
			pauseLevel = 5.0
		else:
			pauseLevel = scene._engineResultView.layerSelect.getValue() * float(profile.getProfileSettingFloat('layer_height'))
		newConfig = {'filename': self.plugin.getFilename(), 'params': { 'pauseLevel': str(pauseLevel) }}
		if not self._buildPluginPanel(newConfig):
			return
		self.pluginConfig.append(newConfig)
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()

	def OnAddLayer(self, e):
		scene = self.GetParent().GetParent().GetParent().GetParent().scene
		if scene.viewMode == 'normal':
			pauseLevelLayer = 2
		else:
			pauseLevelLayer = scene._engineResultView.layerSelect.getValue()
		newConfig = {'filename': self.plugin.getFilename(), 'params': { 'pauseLevelLayer': str(pauseLevelLayer) }}
		if not self._buildPluginPanel(newConfig):
			return
		self.pluginConfig.append(newConfig)
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()

	def OnRem(self, e):
		panel = e.GetEventObject().GetParent()
		sizer = self.pluginEnabledPanel.GetSizer()
		idx = self.panelList.index(panel)

		panel.Show(False)
		for p in self.panelList:
			sizer.Detach(p)
		self.panelList.pop(idx)
		for p in self.panelList:
				sizer.Add(p, flag=wx.EXPAND)

		self.pluginEnabledPanel.Layout()
		self.pluginEnabledPanel.SetSize((1,1))
		self.Layout()

		self.pluginConfig.pop(idx)
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()
