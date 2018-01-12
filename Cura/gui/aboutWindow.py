__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import wx.lib.hyperlink as hl
import platform

from Cura.util import resources

class aboutWindow(wx.Frame):
	def __init__(self, parent):
		super(aboutWindow, self).__init__(parent, title=_("About"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		isWindows = platform.system() == "Windows"

		wx.EVT_CLOSE(self, self.OnClose)

		p = wx.Panel(self)
		self.panel = p
		s = wx.BoxSizer()
		self.SetSizer(s)
		s.Add(p)
		s = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(s)

		title = wx.StaticText(p, -1, 'Cura by Dagoma')
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _('Cura by Dagoma was originally forked from Legacy Cura.\nIt is built with the following components:')), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)

		self.addComponent('LegacyCura', _('Graphical user interface'), 'AGPLv3', 'https://github.com/daid/LegacyCura')
		self.addComponent('CuraEngine', _('GCode Generator'), 'AGPLv3', 'https://github.com/Ultimaker/CuraEngine')
		self.addComponent('Clipper', _('Polygon clipping library'), 'Boost', 'http://www.angusj.com/delphi/clipper.php')
		self.addComponent('Python 2.7', _('Framework'), 'Python', 'http://python.org/')
		self.addComponent('wxPython', _('GUI Framework'), 'wxWindows', 'http://www.wxpython.org/')
		self.addComponent('PyOpenGL', _('3D Rendering Framework'), 'BSD', 'http://pyopengl.sourceforge.net/')
		self.addComponent('PySerial', _('Serial communication library'), 'Python license', 'http://pyserial.sourceforge.net/')
		self.addComponent('NumPy', _('Support library for faster math'), 'BSD', 'http://www.numpy.org/', isWindows)
		if isWindows:
			self.addComponent('VideoCapture', _('Library for WebCam capture'), 'LGPLv2.1', 'http://videocapture.sourceforge.net/')
			self.addComponent('comtypes', _('Library to help with windows taskbar features'), 'MIT', 'http://starship.python.net/crew/theller/comtypes/')
			self.addComponent('EjectMedia', _('Utility to safe-remove SD cards'), 'Freeware', 'http://www.uwe-sieber.de/english.html', False)
		self.Fit()

	def addComponent(self, name, description, license, url, addLine = True):
		p = self.panel
		s = p.GetSizer()
		s.Add(wx.StaticText(p, -1, _('%s: %s (License: %s)') % (name, description, license)), flag=wx.LEFT|wx.RIGHT, border=5)
		s.Add(hl.HyperLinkCtrl(p, wx.ID_ANY, url, URL=url), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		if addLine:
			s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)

	def OnClose(self, e):
		self.Destroy()
