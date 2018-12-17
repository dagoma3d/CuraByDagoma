__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys
import wx

from Cura.util import resources

class warningWindow(wx.Frame):
	def __init__(self, parent, warningMessage):
		super(warningWindow, self).__init__(parent, title=_("Warning"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		self.panel = wx.Panel(self, wx.ID_ANY)

		self.warningMessage = wx.StaticText(self.panel, wx.ID_ANY, warningMessage)
		self.restartNowBtn = wx.Button(self.panel, wx.ID_ANY, _('Restart now'))
		self.restartLaterBtn = wx.Button(self.panel, wx.ID_ANY, _('Restart later'))

		topSizer = wx.BoxSizer(wx.VERTICAL)
		warningSizer = wx.BoxSizer(wx.HORIZONTAL)
		restartSizer = wx.BoxSizer(wx.HORIZONTAL)

		warningSizer.Add(self.warningMessage, 0, flag=wx.ALL, border=5)

		restartSizer.Add(self.restartNowBtn, 0, flag=wx.ALL, border=5)
		restartSizer.Add(self.restartLaterBtn, 0, flag=wx.ALL, border=5)

		topSizer.Add(warningSizer, 0, wx.CENTER)
		topSizer.Add(restartSizer, 0, wx.CENTER)


		self.panel.SetSizer(topSizer)
		topSizer.Fit(self)

		self.Bind(wx.EVT_BUTTON, self.OnRestart, self.restartNowBtn)
		self.Bind(wx.EVT_BUTTON, self.OnClose, self.restartLaterBtn)
		wx.EVT_CLOSE(self, self.OnClose)

	def OnClose(self, e):
		self.Destroy()

	def OnRestart(self, e):
		print 'OnRestart handler'
		try:
			python = sys.executable
			#python = "'" + sys.executable + "'"
			#print python
			#print sys.argv
			python = python.split('"')
			if len(python) > 1:
				python = python[1]
			else:
				python = python[0]
			print python
			os.execl(python, '"' + python + '"', *sys.argv)
		except:
			self.Destroy()
