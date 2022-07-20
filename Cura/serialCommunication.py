"""
Serial communication with the printer for printing is done from a separate process,
this to ensure that the PIL does not block the serial printing.

This file is the 2nd process that is started to handle communication with the printer.
And handles all communication with the initial process.
"""

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import sys
import time
import os
import json

from Cura.util import machineCom
from Cura.util import profile

class serialComm(object):
	"""
	The serialComm class is the interface class which handles the communication between stdin/stdout and the machineCom class.
	This interface class is used to run the (USB) serial communication in a different process then the GUI.
	"""
	def __init__(self, portName, baudrate):
		self._comm = None
		self._gcodeList = []

		try:
			baudrate = int(baudrate)
		except ValueError:
			baudrate = 0
		self._comm = machineCom.MachineCom(portName, baudrate, callbackObject=self)

	def mcLog(self, message):
		result = ('log:%s\n' % (message)).encode()
		sys.stdout.write(result)

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		result = ('temp:%s:%s:%f:%f\n' % (json.dumps(temp), json.dumps(targetTemp), bedTemp, bedTargetTemp)).encode()
		sys.stdout.write(result)

	def mcStateChange(self, state):
		if self._comm is None:
			return
		result = ('state:%d:%s\n' % (state, self._comm.getStateString())).encode()
		sys.stdout.write(result)

	def mcMessage(self, message):
		result = ('message:%s\n' % (message)).encode()
		sys.stdout.write(result)

	def mcProgress(self, lineNr):
		result = ('progress:%d\n' % (lineNr)).encode()
		sys.stdout.write(result)

	def mcZChange(self, newZ):
		result = ('changeZ:%d\n' % (newZ)).encode()
		sys.stdout.write(result)

	def monitorStdin(self):
		while not self._comm.isClosed():
			line = sys.stdin.readline().strip()
			line = line.split(':', 1)
			if line[0] == 'STOP':
				self._comm.cancelPrint()
				self._gcodeList = ['M110']
			elif line[0] == 'G':
				self._gcodeList.append(line[1])
			elif line[0] == 'C':
				self._comm.sendCommand(line[1])
			elif line[0] == 'START':
				self._comm.printGCode(self._gcodeList)
			elif line[0] == 'CANCEL':
				self._comm.printGCode(self._gcodeList)
			elif line[0] == 'PAUSE':
				self._comm.setPause(True)
				self._comm.printGCode(self._gcodeList)
			elif line[0] == 'RESUME':
				self._comm.setPause(False)
				self._comm.printGCode(self._gcodeList)
			else:
				sys.stderr.write(str(line))

def startMonitor(portName, baudrate):
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
	comm = serialComm(portName, baudrate)
	comm.monitorStdin()

def main():
	if len(sys.argv) != 3:
		return
	portName, baudrate = sys.argv[1], sys.argv[2]
	startMonitor(portName, baudrate)

if __name__ == '__main__':
	main()
