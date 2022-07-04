from ctypes import *
import sys


class Battery():
    def __init__(self):

        # default values
        self.charging = False
        self.percent = -1

        if sys.platform.startswith('win'):
            batteryWindows = BatteryWindows()
            windll.kernel32.GetSystemPowerStatus(byref(batteryWindows))
            self.charging = bool(batteryWindows.ACLineStatus)
            self.percent = batteryWindows.BatteryLifePercent

        else:
            import subprocess
            # execute "pmset -g batt" and extract the power percent and the status of the battery
            infos = subprocess.check_output(["pmset -g batt"]).split(b'\t')[1].split(b'; ').decode()
            self.charging = infos[1] != 'discharging'
            self.percent = int(infos[0][:-1])

    def isLow(self):
        # warning if under 33% and not charging
        if self.charging is None or self.percent == -1: # failed to read battery status
            return None
        else:
            return (not self.charging) and self.percent <= 33


class BatteryWindows(Structure):
    # necessary to get Battery infos on Windows using ctypes
    _fields_ = [('ACLineStatus', c_byte),
            ('BatteryFlag', c_byte),
            ('BatteryLifePercent', c_byte),
            ('Reserved1',c_byte),
            ('BatteryLifeTime',c_ulong),
            ('BatteryFullLifeTime',c_ulong)] 
