__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

def StupidMacOSWorkaround():
	"""
	On MacOS for some magical reason opening new frames does not work until you opened a new modal dialog and closed it.
	If we do this from software, then, as if by magic, the bug which prevents opening extra frames is gone.
	"""
	dlg = wx.Dialog(None)
	wx.PostEvent(dlg, wx.CommandEvent(wx.EVT_CLOSE.typeId))
	dlg.ShowModal()
	dlg.Destroy()
