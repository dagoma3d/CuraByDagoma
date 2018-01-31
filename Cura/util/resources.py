"""
Helper module to get easy access to the path where resources are stored.
This is because the resource location is depended on the packaging method and OS
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys
import glob
import gettext

if sys.platform.startswith('darwin'):
	try:
		#Foundation import can crash on some MacOS installs
		from Foundation import *
	except:
		pass

if sys.platform.startswith('darwin'):
	if hasattr(sys, 'frozen'):
		try:
			resourceBasePath = NSBundle.mainBundle().resourcePath()
		except:
			resourceBasePath = os.path.join(os.path.dirname(__file__), "../../../../../")
	else:
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")
else:
	resourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")

def getPathForResource(dir, subdir, resource_name):
	assert os.path.isdir(dir), "{p} is not a directory".format(p=dir)
	path = os.path.normpath(os.path.join(dir, subdir, resource_name))
	assert os.path.isfile(path), "{p} is not a file.".format(p=path)
	return path

def getPathForImage(name):
	return getPathForResource(resourceBasePath, 'images', name)

def getPathForMesh(name):
	return getPathForResource(resourceBasePath, 'meshes', name)

def getPathForFirmware(name):
	return getPathForResource(resourceBasePath, 'firmware', name)

def getPathForXML(name):
	return getPathForResource(resourceBasePath, 'XML', name)

def setupLocalization(selectedLanguage = None):
	#Default to english
	languages = ['en']

	if selectedLanguage is not None:
		for item in getLanguageOptions():
			if item[1] == selectedLanguage and item[0] is not None:
				languages = [item[0]]

	locale_path = os.path.normpath(os.path.join(resourceBasePath, 'locale'))
	translation = gettext.translation('Cura', locale_path, languages, fallback=True)
	translation.install(unicode=True)

def getLanguageOptions():
	return [
		['en', 'English'],
		['fr', 'French']
	]

def getPrinterOptions(internalUse = 'False'):
	discoeasy200 = {
		'name': 'DiscoEasy200',
		'desc': 'DiscoEasy200',
		'config': 'discoeasy200.xml',
		'img': 'discoeasy200.png'
	}

	discovery200 = {
		'name': 'DiscoVery200',
		'desc': 'DiscoVery200',
		'config': 'discovery200.xml',
		'img': 'discovery200.png'
	}

	explorer350 = {
		'name': 'Explorer350',
		'desc': 'Explorer350',
		'config': 'explorer350.xml',
		'img': 'explorer350.png'
	}

	neva = {
		'name': 'Neva',
		'desc': 'Neva (No serial number)',
		'config': 'neva.xml',
		'img': 'neva.png'
	}

	neva_sn6000 = {
		'name': 'Neva',
		'desc': 'Neva (Serial number > 6000)',
		'config': 'neva_sn6000.xml',
		'img': 'neva.png'
	}

	printerOptions = []
	printerOptions.append(discovery200)
	printerOptions.append(discoeasy200)
	if internalUse == 'True':
		printerOptions.append(explorer350)
	printerOptions.append(neva)
	printerOptions.append(neva_sn6000)
	return printerOptions
