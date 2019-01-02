__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import wx.lib.hyperlink as hl

from Cura.util import profile
from Cura.util import resources

class forbiddenWindow(wx.Frame):
	def __init__(self, parent):
		super(forbiddenWindow, self).__init__(parent, title=_("Warning"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

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

		s.Add(wx.StaticText(p, -1, _("You have tried to load some weird files...")), flag=wx.ALIGN_CENTRE|wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("We don't want these objects to be printed by our products.")), flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("Please follow the link below for additional information.")), flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(hl.HyperLinkCtrl(p, wx.ID_ANY, _("More details..."), URL=profile.getPreference('warning_url')), flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		self.Fit()

	def OnClose(self, e):
		self.Destroy()
