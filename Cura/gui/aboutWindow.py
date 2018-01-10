__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import platform

class aboutWindow(wx.Frame):
	def __init__(self):
		super(aboutWindow, self).__init__(None, title=_("About"), style = wx.DEFAULT_DIALOG_STYLE)

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
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.EXPAND|wx.BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)

		s.Add(wx.StaticText(p, -1, 'End solution for Open Source Fused Filament Fabrication 3D printing.'), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, 'Cura by Dagoma was originally forked from Legacy Cura'), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)

		s.Add(wx.StaticText(p, -1, 'Cura by Dagoma is built with the following components:'), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		self.addComponent('LegacyCura', 'Graphical user interface', 'AGPLv3', 'https://github.com/daid/LegacyCura')
		self.addComponent('CuraEngine', 'GCode Generator', 'AGPLv3', 'https://github.com/Ultimaker/CuraEngine')
		self.addComponent('Clipper', 'Polygon clipping library', 'Boost', 'http://www.angusj.com/delphi/clipper.php')

		self.addComponent('Python 2.7', 'Framework', 'Python', 'http://python.org/')
		self.addComponent('wxPython', 'GUI Framework', 'wxWindows', 'http://www.wxpython.org/')
		self.addComponent('PyOpenGL', '3D Rendering Framework', 'BSD', 'http://pyopengl.sourceforge.net/')
		self.addComponent('PySerial', 'Serial communication library', 'Python license', 'http://pyserial.sourceforge.net/')
		self.addComponent('NumPy', 'Support library for faster math', 'BSD', 'http://www.numpy.org/')
		if platform.system() == "Windows":
			self.addComponent('VideoCapture', 'Library for WebCam capture on windows', 'LGPLv2.1', 'http://videocapture.sourceforge.net/')
			#self.addComponent('ffmpeg', 'Support for making timelaps video files', 'GPL', 'http://www.ffmpeg.org/')
			self.addComponent('comtypes', 'Library to help with windows taskbar features on Windows 7', 'MIT', 'http://starship.python.net/crew/theller/comtypes/')
			self.addComponent('EjectMedia', 'Utility to safe-remove SD cards', 'Freeware', 'http://www.uwe-sieber.de/english.html')
		self.addComponent('Pymclevel', 'Python library for reading Minecraft levels.', 'ISC', 'https://github.com/mcedit/pymclevel')
		self.Fit()

	def addComponent(self, name, description, license, url):
		p = self.panel
		s = p.GetSizer()
		s.Add(wx.StaticText(p, -1, '* %s - %s' % (name, description)), flag=wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, '   License: %s - Website: %s' % (license, url)), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)

	def OnClose(self, e):
		self.Destroy()
