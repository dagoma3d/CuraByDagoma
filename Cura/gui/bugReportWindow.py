__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import wx.lib.agw.hyperlink as hl
from Cura.util import resources

class bugReportWindow(wx.Frame):
	def __init__(self, parent):
		super(bugReportWindow, self).__init__(parent, title=_("Report a bug"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

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

		title = wx.StaticText(p, -1, _("How to report a problem ?"))
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("If you have noticed a problem, please first ensure you are using the latest version of Cura By Dagoma.")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("To report the problem to the IT staff, please follow this link to create an Issue on GitHub :")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		url_github_issues = "https://github.com/dagoma3d/CuraByDagoma/issues"
		s.Add(hl.HyperLinkCtrl(p, wx.ID_ANY, url_github_issues, URL=url_github_issues), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("If you don't feel confident with the GitHub platform, you can also create a support ticket from the dagoma's website :")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		url_dagoma_tickets = "https://www.dagoma3d.com/creation-de-ticket"
		s.Add(hl.HyperLinkCtrl(p, wx.ID_ANY, url_dagoma_tickets, URL=url_dagoma_tickets), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("Before explaining the problem, please write the version of your OS.")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("If the problem happens after loading a certain STL file, please attach it to your message.")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("If it's possible, attach the last (or the previous) STL you have loaded too.")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("Then, please attach the 3 files named : 'current_profile.ini', 'mru_filelist.ini', 'preferences.ini'.\n- On Windows, you can find them in ~/.curaByDagoma/2.2.0/.\n- On MacOs, you can find them in ~/Library/Application Support/CuraByDagoma/2.2.0/.\n- On Linux, you can find them in ~/.curaByDagoma/2.2.0/.")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _("After sending your message, please check regularly in case someone has answered you. We will try to solve your problem as soon as possible.")), flag=wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)

		self.Fit()

	def OnClose(self, e):
		self.Destroy()