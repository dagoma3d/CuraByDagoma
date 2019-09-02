# coding=utf-8
#Name: Pause at (ByDagoma)
#Info: Add pause at a given height or layer
#Depend: GCode
#Type: postprocess
#Param: pauseLevelLayer(int:-1) Set a layer number

__copyright__ = "Copyright (C) 2016 Dagoma.Fr - Released under terms of the AGPLv3 License"
import re
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
#state 2 system found the layer it need to write. We will wait for the first G1 or G0 code to write the content just before. state will be set to 0

#Param: pauseLevel(float:-1.0) Pause height (mm)
try:
	pauseLevel_i = float(pauseLevel)
except:
	pauseLevel_i = -1.0

try:
	pauseLevelLayer_i = int(pauseLevelLayer)
except:
	pauseLevelLayer_i = -1

with open(filename, "w") as f:
	lineIndex = 0
	lastLayerIndex = 99999
	layerZ = 0
	for lIndex in xrange(len(lines)):
		line = lines[lIndex]
		if line.startswith(';'):
			if line.startswith(';LAYER:'):
				currentLayer = int(line[7:].strip()) + 1

				if currentLayer < lastLayerIndex:
					pauseState = 1

				lastLayerIndex = currentLayer
				if pauseState == 1:
					if pauseLevelLayer_i > -1:
						if lastLayerIndex == pauseLevelLayer_i:
							pauseState = 2
					elif pauseLevel_i > -1:
						layerZ = getPrintZValue(lines[lIndex:lIndex+20])
						if layerZ >= pauseLevel_i:
							pauseState = 2

			f.write(line)
			continue

		x = getValue(line, 'X', x)
		y = getValue(line, 'Y', y)

		if pauseState == 2:
			g = getValue(line, 'G', None)
			if g == 1 or g == 0:# We will do the pause just before printing content. We need to pause from the previous XY position. Not the current.
				z = layerZ

				pauseState = 0
				f.write(";TYPE:CUSTOM\n")
				#Retract
				if profile.getMachineSetting('machine_name') in ['Neva', 'Magis']:
					f.write("M600 U-55 X55 Y-92 Z60\r\n")
				else:
					f.write("M600 L0 PA\r\n")

		f.write(line)
