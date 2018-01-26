"""
Helper module to get easy access to the xml config file.
"""
__copyright__ = "Copyright (C) 2017 Orel - Released under terms of the AGPLv3 License"

from Cura.util import resources
from xml.dom import minidom

configuration = minidom.parse(resources.getPathForXML('neva.xml'))

def getTags(name, parent = configuration):
	try:
		return parent.getElementsByTagName(name)
	except:
		return []

def getTag(name, parent = configuration, i = 0):
	try:
		return parent.getElementsByTagName(name)[i]
	except:
		return None

def getValue(name, parent = configuration, i = 0):
	try:
		if type(parent) is str:
			return getTag(parent).getElementsByTagName(name)[i].childNodes[0].data
		else:
			return parent.getElementsByTagName(name)[i].childNodes[0].data
	except:
		return None

def getAttribute(name, tag_name, i = 0):
	try:
		return configuration.getElementsByTagName(tag_name)[i].getAttribute(name)
	except:
		return ''
