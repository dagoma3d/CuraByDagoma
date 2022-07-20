__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import sys
import os
import platform
import shutil
import glob
import warnings

try:
	#Only try to import the _core to save import time
	import wx._core
except ImportError:
	import wx

class CuraApp(wx.App):
	def __init__(self, files):
		if platform.system() == "Windows" and not 'PYCHARM_HOSTED' in os.environ:
			basePath = os.path.normpath(os.path.expanduser('~/.curaByDagoma/' + os.environ['CURABYDAGO_VERSION']))
			super(CuraApp, self).__init__(redirect=False)
		else:
			super(CuraApp, self).__init__(redirect=False)

		self.mainWindow = None
		self.splash = None
		self.loadFiles = files

		self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

		if sys.platform.startswith('win'):
			#Check for an already running instance, if another instance is running load files in there
			from Cura.util import version
			from ctypes import windll
			import ctypes
			import socket
			import threading

			portNr = 0xCA00 + sum(map(ord, version.getVersion(False)))
			if len(files) > 0:
				try:
					other_hwnd = windll.user32.FindWindowA(None, ctypes.c_char_p('Cura - ' + version.getVersion()))
					if other_hwnd != 0:
						sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						sock.sendto('\0'.join(files), ("127.0.0.1", portNr))

						windll.user32.SetForegroundWindow(other_hwnd)
						return
				except:
					pass

			socketListener = threading.Thread(target=self.Win32SocketListener, args=(portNr,))
			socketListener.daemon = True
			socketListener.start()

		if sys.platform.startswith('darwin'):
			#Do not show a splashscreen on OSX, as by Apple guidelines
			self.afterSplashCallback()
		else:
			from Cura.gui import splashScreen
			self.splash = splashScreen.splashScreen(self.afterSplashCallback)

	def MacOpenFile(self, path):
		try:
			self.mainWindow.OnDropFiles([path])
		except Exception as e:
			warnings.warn("File at {p} cannot be read: {e}".format(p=path, e=str(e)))

	def MacReopenApp(self, event):
		self.GetTopWindow().Raise()

	def MacHideApp(self, event):
		self.GetTopWindow().Show(False)

	def MacNewFile(self):
		pass

	def MacPrintFile(self, file_path):
		pass

	def OnActivate(self, e):
		if e.GetActive():
			self.GetTopWindow().Raise()
		e.Skip()

	def Win32SocketListener(self, port):
		import socket
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.bind(("127.0.0.1", port))
			while True:
				data, addr = sock.recvfrom(2048)
				self.mainWindow.OnDropFiles(data.split('\0'))
		except:
			pass

	def afterSplashCallback(self):
		#These imports take most of the time and thus should be done after showing the splashscreen
		from Cura.gui import configWizard
		from Cura.util import profile
		from Cura.util import resources
		# it's important to set up localization at very beginning to install
		language = profile.getPreference('language')
		resources.setupLocalization(language)

		if self.splash is not None:
			self.splash.Show(False)
			self.splash = None

		#If we haven't run it before, run the configuration wizard.
		if profile.getMachineSetting('machine_name') == '':
			configWizard.ConfigWizard()
			#Check if we need to copy our examples
			exampleFile = os.path.normpath(os.path.join(resources.resourceBasePath, 'example', 'dagoma.stl'))
			self.loadFiles = [exampleFile]

		from Cura.gui import mainWindow
		self.mainWindow = mainWindow.mainWindow()
		self.SetTopWindow(self.mainWindow)
		self.mainWindow.Show()
		self.mainWindow.OnDropFiles(self.loadFiles)

		setFullScreenCapable(self.mainWindow)

if platform.system() == "Darwin": #Mac magic. Dragons live here. THis sets full screen options.
	try:
		import ctypes, objc
		_objc = ctypes.PyDLL(objc._objc.__file__)

		# PyObject *PyObjCObject_New(id objc_object, int flags, int retain)
		_objc.PyObjCObject_New.restype = ctypes.py_object
		_objc.PyObjCObject_New.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

		def setFullScreenCapable(frame):
			frameobj = _objc.PyObjCObject_New(frame.GetHandle(), 0, 1)

			NSWindowCollectionBehaviorFullScreenPrimary = 1 << 7
			NSWindowCollectionBehaviorFullScreenAuxiliary = 1 << 8
			window = frameobj.window()
			newBehavior = window.collectionBehavior() | NSWindowCollectionBehaviorFullScreenAuxiliary
			window.setCollectionBehavior_(newBehavior)
	except:
		def setFullScreenCapable(frame):
			pass

else:
	def setFullScreenCapable(frame):
		pass
