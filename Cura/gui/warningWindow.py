__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.util import resources

class warningWindow(wx.Frame):
	def __init__(self, parent, warningMessage):
		super(warningWindow, self).__init__(parent, title=_("Warning"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		wx.EVT_CLOSE(self, self.OnClose)

		p = wx.Panel(self)
		self.panel = p
		s = wx.BoxSizer()
		self.SetSizer(s)
		s.Add(p)
		s = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(s)

		#s.Add(title, flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1,warningMessage), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		self.Fit()

	def OnClose(self, e):
		self.Destroy()
