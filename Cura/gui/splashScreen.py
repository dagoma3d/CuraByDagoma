__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx._core #We only need the core here, which speeds up the import. As we want to show the splashscreen ASAP.
from   wx.adv import SplashScreen

from Cura.util.resources import getPathForImage

class splashScreen(SplashScreen):
	def __init__(self, callback):
		self.callback = callback
		bitmap = wx.Bitmap(getPathForImage('splash.png'))
		super(splashScreen, self).__init__(bitmap, wx.adv.SPLASH_CENTRE_ON_SCREEN, 0, None)
		wx.CallAfter(self.DoCallback)

	def DoCallback(self):
		self.callback()
		if self:
			self.Destroy()
