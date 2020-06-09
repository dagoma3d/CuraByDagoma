__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import wx.lib.agw.hyperlink as hl

from Cura.util import profile
from Cura.util import resources

class forbiddenWindow(wx.Frame):
	def __init__(self, parent, nbForbiddenFiles):
		super(forbiddenWindow, self).__init__(parent, title=_("Warning"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

		frameicon = wx.Icon(resources.getPathForImage('cura.ico'), wx.BITMAP_TYPE_ICO)
		self.SetIcon(frameicon)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

		p = wx.Panel(self)
		self.panel = p
		s = wx.BoxSizer()
		self.SetSizer(s)
		s.Add(p)
		s = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(s)

		self.more_details_url = hl.HyperLinkCtrl(p, wx.ID_ANY, _("More details..."), URL=_("warning_url"))
		#hl.EVT_HYPERLINK_LEFT(self, self.more_details_url.GetId(), self.OnClick)
		self.more_details_url.AutoBrowse(False)
		self.more_details_url.Bind(hl.EVT_HYPERLINK_LEFT, self.OnClick)

		img = wx.Image(resources.getPathForImage('forbidden.png'), wx.BITMAP_TYPE_PNG)
		s.Add(wx.StaticBitmap(p, -1, wx.BitmapFromImage(img)), flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("Our software doest not allow the printing of 3D weapons.")), flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(self.more_details_url, flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		self.Fit()

	def OnClose(self, e):
		self.Destroy()

	def OnClick(self, e):
		self.more_details_url.GotoURL(self.more_details_url.GetURL())
		self.Destroy()
