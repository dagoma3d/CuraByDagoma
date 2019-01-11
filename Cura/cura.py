#!/usr/bin/python
"""
This page is in the table of contents.
==Overview==
===Introduction===
Cura is a AGPL tool chain to generate a GCode path for 3D printing. Older versions of Cura where based on Skeinforge.
Versions up from 13.05 are based on a C++ engine called CuraEngine.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

from optparse import OptionParser

import sys
import os

os.environ['CURABYDAGO_RELEASE_VERSION'] = '2.1.2'
os.environ['CURABYDAGO_BUILD_VERSION'] = 'a2'
os.environ['CURABYDAGO_VERSION'] = os.environ['CURABYDAGO_RELEASE_VERSION'] + os.environ['CURABYDAGO_BUILD_VERSION']


# Is it the first run after installation
if sys.platform.startswith('darwin'):
	try:
		#Foundation import can crash on some MacOS installs
		from Foundation import *
	except:
		pass

	if hasattr(sys, 'frozen'):
		try:
			myResourceBasePath = NSBundle.mainBundle().resourcePath()
		except:
			myResourceBasePath = os.path.join(os.path.dirname(__file__), "../../../../../")
	else:
		myResourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")

	newinstallfile = os.path.normpath(os.path.join(myResourceBasePath, 'new'))
	if os.path.isfile(newinstallfile):
		try:
			os.remove(newinstallfile)
			current_profile_inifile = os.path.expanduser('~/Library/Application Support/CuraByDagoma/' + os.environ['CURABYDAGO_VERSION'] + '/current_profile.ini')
			if os.path.isfile(current_profile_inifile):
				os.remove(current_profile_inifile)
			preferences_inifile = os.path.expanduser('~/Library/Application Support/CuraByDagoma/' + os.environ['CURABYDAGO_VERSION'] + '/preferences.ini')
			if os.path.isfile(preferences_inifile):
				os.remove(preferences_inifile)
		except:
			pass

from Cura.util import profile

def main():
	"""
	Main Cura entry point. Parses arguments, and starts GUI or slicing process depending on the arguments.
	"""
	parser = OptionParser(usage="usage: %prog [options] <filename>.stl")
	parser.add_option("-i", "--ini", action="store", type="string", dest="profileini",
		help="Load settings from a profile ini file")
	parser.add_option("-r", "--print", action="store", type="string", dest="printfile",
		help="Open the printing interface, instead of the normal cura interface.")
	parser.add_option("-p", "--profile", action="store", type="string", dest="profile",
		help="Internal option, do not use!")
	parser.add_option("-s", "--slice", action="store_true", dest="slice",
		help="Slice the given files instead of opening them in Cura")
	parser.add_option("-o", "--output", action="store", type="string", dest="output",
		help="path to write sliced file to")
	parser.add_option("--serialCommunication", action="store", type="string", dest="serialCommunication",
		help="Start commandline serial monitor")

	(options, args) = parser.parse_args()

	if options.serialCommunication:
		from Cura import serialCommunication
		port, baud = options.serialCommunication.split(':')
		serialCommunication.startMonitor(port, baud)
		return

	print ("Load preferences from " + profile.getPreferencePath())
	profile.loadPreferences(profile.getPreferencePath())

	if options.profile is not None:
		profile.setProfileFromString(options.profile)
	elif options.profileini is not None:
		profile.loadProfile(options.profileini)
	else:
		profile.loadProfile(profile.getDefaultProfilePath(), True)

	if options.printfile is not None:
		from Cura.gui import printWindow
		printWindow.startPrintInterface(options.printfile)
	elif options.slice is not None:
		from Cura.util import sliceEngine
		from Cura.util import objectScene
		from Cura.util import meshLoader
		import shutil

		def commandlineProgressCallback(progress):
			if progress >= 0:
				#print 'Preparing: %d%%' % (progress * 100)
				pass
		scene = objectScene.Scene()
		scene.updateMachineDimensions()
		engine = sliceEngine.Engine(commandlineProgressCallback)
		for m in meshLoader.loadMeshes(args[0]):
			scene.add(m)
		engine.runEngine(scene)
		engine.wait()

		if not options.output:
			options.output = args[0] + profile.getGCodeExtension()
		with open(options.output, "wb") as f:
			f.write(engine.getResult().getGCode())
		print ('GCode file saved : %s' % options.output)

		engine.cleanup()
	else:
		from Cura.gui import app
		app.CuraApp(args).MainLoop()

if __name__ == '__main__':
	main()
