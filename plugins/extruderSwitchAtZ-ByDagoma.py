# coding=utf-8
#Name: Pause at (ByDagoma)
#Info: Switch between extruder height or layer
#Depend: GCode
#Type: postprocess
#Param: extruderSwitchLevelLayer(int:-1) Set a layer number

__copyright__ = "Copyright (C) 2016 Dagoma.Fr - Released under terms of the AGPLv3 License"
import re
import os
from Cura.util import profile

def getPrintZValue(lineBlock):
	'''
	look for the last z value found just before (or at the same time) G1 code in the given block
	'''
	lastZ = -1
	for line in lineBlock:
		lastZ = getValue(line, 'Z', lastZ)
		if line.startswith('G1 ') and (getValue(line, 'X', None) is not None or getValue(line, 'Y', None) is not None):
			break

	return lastZ


def getValue(line, key, default = None):
	if not key in line or (';' in line and line.find(key) > line.find(';')):
		return default
	subPart = line[line.find(key) + 1:]
	m = re.search('^[0-9]+\.?[0-9]*', subPart)
	if m is None:
		return default
	try:
		return float(m.group(0))
	except:
		return default

with open(filename, "r") as f:
	lines = f.readlines()

z = 0.
x = 0.
y = 0.
pauseState = 0
#state 0 system is not active until we get to a smaller layer than the last encountered layer (default at 99999) (print one at a time support.)
#state 1 system is active and we are looking for our target layer z
#state 2 system found the layer it need to write. We will switch extruder. state will be set to 0

try:
	extruderSwitchLevelLayer_i = int(extruderSwitchLevelLayer)
except:
	extruderSwitchLevelLayer_i = -1

with open(filename, "w") as f:
	lineIndex = 0
	lastLayerIndex = 99999
	lastG1 = ""
	currentExtruder = ""
	for lIndex in range(len(lines)):
		line = lines[lIndex]
		if line.startswith('T'):
			currentExtruder = line.split(" ")[0]

		if line.startswith(';'):
			if line.startswith(';LAYER:'):
				currentLayer = int(line[7:].strip()) + 1
				# We are assuming there is always this sequence:
				# G1 F2100 X122.906 Y58.862 E1750.80156
				# ;LAYER:27
				lastG1 = lines[lIndex-1].split()[-1]

				if currentLayer < lastLayerIndex:
					pauseState = 1

				lastLayerIndex = currentLayer
				if pauseState == 1:
					if extruderSwitchLevelLayer_i > -1:
						if lastLayerIndex == extruderSwitchLevelLayer_i:
							pauseState = 2

			f.write(line)
			continue

		if pauseState == 2:
			g = getValue(line, 'G', None)
			if g == 1 or g == 0: # We will do the extruder switch just before printing content. We need to switch from the previous XY position. Not the current.
				newExtruder = "T1" if currentExtruder == "T0" else "T0"
				pauseState = 0
				f.write(';TYPE:CUSTOM\n')
				f.write('G92 E0 ;Set current extruder position to 0\n')
				# FIXME: This should make sure we free the correct extruder
				f.write('G1 E-60 F3000 ;Free the nozzle from filament of extruder ' + currentExtruder + '\n')
				f.write(newExtruder + ' ;Switch extruder\n')
				f.write('G92 E0 ;Set current extruder position to 0\n')
				# FIXME: This should make sure we free the correct extruder
				f.write('G1 E60 F3000 ;Engage the filement of extruder ' + newExtruder + ' in the nozzle\n')
				f.write('G92 ' + lastG1 + ' ;Set the extruder position to the last known position\n')
				currentExtruder = newExtruder

		f.write(line.rstrip() + os.linesep)
