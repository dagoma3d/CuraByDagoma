__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
from Cura.util import resources

class shortcutsWindow(wx.Frame):
	def __init__(self, parent):
		super(shortcutsWindow, self).__init__(parent, title=_("Shortcuts"), style = wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT)

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

		title = wx.StaticText(p, -1, _("Shortcuts"))
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)
		s.Add(wx.StaticText(p, -1, _('Here is a list of shortcuts to help moving camera through the scene and applying transformations with the tools.')), flag=wx.ALIGN_CENTER|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)

		self.addSection(_("Moving Camera"))
		self.addComponent(_('Right click'), _('Rotate the camera (drag the mouse)'))
		self.addComponent('Shift + ' + _('Right click'), _('Translate the camera (drag the mouse)'))
		self.addSection(_("Rotate Tool"))
		self.addComponent(_('Left click'), _('Rotate the object (drag the mouse along a circle)'))
		self.addComponent('Shift + ' + _('Left click'), _('Rotate the object slowly (drag the mouse along a circle)'))
		self.addSection(_("Scale Tool"))
		self.addComponent(_('Left click'), _("Modify the object's size (drag the mouse from the end of an axis)"))
		self.addComponent('Shift + ' + _('Left click'), _("Modify the object's size slowly (drag the mouse from the end of an axis)"))
		self.addComponent('Ctrl + ' + _('Left click'), _("Stretch the object (drag the mouse from the end of an axis)"))
		self.addComponent('Ctrl + ' + 'Shift + ' + _('Left click'), _("Stretch the object slowly (drag the mouse from the end of an axis)"))

		self.Fit()

	def addSection(self, section):
		p = self.panel
		s = p.GetSizer()
		staticText = wx.StaticText(p, -1, section)
		staticText.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=5)
		s.Add(staticText, flag=wx.ALIGN_CENTRE|wx.BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)

	def addComponent(self, shortcut, description):
		p = self.panel
		s = p.GetSizer()
		line = wx.BoxSizer(wx.HORIZONTAL)
		shortcutLabel = wx.StaticText(p, -1, shortcut)
		shortcutLabel.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))
		line.Add(shortcutLabel)
		descriptionLabel = wx.StaticText(p, -1, ' : ' + description)
		line.Add(descriptionLabel)
		s.Add(line, flag=wx.LEFT|wx.RIGHT, border=5)

	def OnClose(self, e):
		self.Destroy()
