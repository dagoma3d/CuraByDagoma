#!/usr/bin/python

import os, sys

sys.path.insert(1, os.path.dirname(__file__))
os.environ['GDK_BACKEND'] = 'x11'
os.environ['PYOPENGL_PLAFORM'] = 'x11'

try:
	import OpenGL
	import wx
	import serial
	import numpy
except ImportError as e:
	print(e.message)
	if e.message[0:16] == 'No module named ':
		module = e.message[16:]

		if module == 'OpenGL':
			module = 'PyOpenGL'
		elif module == 'serial':
			module = 'pyserial'
		print('Requires ' + module)
		print("Try sudo easy_install " + module)
		print(e.message)

	exit(1)


import Cura.cura as cura

cura.main()
