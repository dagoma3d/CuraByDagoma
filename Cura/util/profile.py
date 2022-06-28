# coding=utf-8
"""
The profile module contains all the settings for Cura.
These settings can be globally accessed and modified.
"""

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import traceback
import math
import re
import zlib
import base64
import time
import sys
import platform
import glob
import string
import stat
import types
import numpy
import locale
if sys.version_info[0] < 3:
	import ConfigParser
else:
	import configparser as ConfigParser

from Cura.util import version
from Cura.util import validators
from Cura.util import resources

#The settings dictionary contains a key/value reference to all possible settings. With the setting name as key.
settingsDictionary = {}
#The settings list is used to keep a full list of all the settings. This is needed to keep the settings in the proper order,
# as the dictionary will not contain insertion order.
settingsList = []
# Merge done or not
mergeDone = False

#Currently selected machine (by index) Cura support multiple machines in the same preferences and can switch between them.
# Each machine has it's own index and unique name.
_selectedMachineIndex = 0

class setting(object):
	"""
		A setting object contains a configuration setting. These are globally accessible trough the quick access functions
		and trough the settingsDictionary function.
		Settings can be:
		* profile settings (settings that effect the slicing process and the print result)
		* preferences (settings that effect how cura works and acts)
		* machine settings (settings that relate to the physical configuration of your machine)
		* alterations (bad name copied from Skeinforge. These are the start/end code pieces)
		Settings have validators that check if the value is valid, but do not prevent invalid values!
		Settings have conditions that enable/disable this setting depending on other settings. (Ex: Dual-extrusion)
	"""
	def __init__(self, name, default, type, category, subcategory):
		self._name = name
		self._label = name
		self._tooltip = ''
		self._default = str(default)
		self._values = []
		self._type = type
		self._category = category
		self._subcategory = subcategory
		self._validators = []
		self._conditions = []

		if type is float:
			validators.validFloat(self)
		elif type is int:
			validators.validInt(self)

		global settingsDictionary
		settingsDictionary[name] = self
		global settingsList
		settingsList.append(self)

	def setLabel(self, label, tooltip = ''):
		self._label = label
		self._tooltip = tooltip
		return self

	def setRange(self, minValue=None, maxValue=None):
		if len(self._validators) < 1:
			return
		self._validators[0].minValue = minValue
		self._validators[0].maxValue = maxValue
		return self

	def getLabel(self):
		return _(self._label)

	def getTooltip(self):
		return _(self._tooltip)

	def getCategory(self):
		return self._category

	def getSubCategory(self):
		return self._subcategory

	def isPreference(self):
		return self._category == 'preference'

	def isMachineSetting(self):
		return self._category == 'machine'

	def isAlteration(self):
		return self._category == 'alteration'

	def isProfile(self):
		return not self.isAlteration() and not self.isPreference() and not self.isMachineSetting()

	def getName(self):
		return self._name

	def getType(self):
		return self._type

	def getValue(self, index = None):
		if index is None:
			index = self.getValueIndex()
		if index >= len(self._values):
			return self._default
		return self._values[index]

	def getDefault(self):
		return self._default

	def setValue(self, value, index = None):
		if index is None:
			index = self.getValueIndex()
		while index >= len(self._values):
			self._values.append(self._default)
		self._values[index] = str(value)

	def getValueIndex(self):
		if self.isMachineSetting() or self.isProfile() or self.isAlteration():
			global _selectedMachineIndex
			return _selectedMachineIndex
		return 0

	def validate(self):
		result = validators.SUCCESS
		msgs = []
		for validator in self._validators:
			res, err = validator.validate()
			if res == validators.ERROR:
				result = res
			elif res == validators.WARNING and result != validators.ERROR:
				result = res
			if res != validators.SUCCESS:
				msgs.append(err)
		return result, '\n'.join(msgs)

	def addCondition(self, conditionFunction):
		self._conditions.append(conditionFunction)

	def checkConditions(self):
		for condition in self._conditions:
			if not condition():
				return False
		return True

#########################################################
## Settings
#########################################################

#Define a fake _() function to fake the gettext tools in to generating strings for the profile settings.
def _(n):
	return n

setting('layer_height',              0.1, float, 'basic',    _('Quality')).setRange(0.0001).setLabel(_("Layer height (mm)"), _("Layer height in millimeters.\nThis is the most important setting to determine the quality of your print. Normal quality prints are 0.1mm, high quality is 0.06mm. You can go up to 0.25mm with an Ultimaker for very fast prints at low quality."))
setting('wall_thickness',            0.8, float, 'basic',    _('Quality')).setRange(0.0).setLabel(_("Shell thickness (mm)"), _("Thickness of the outside shell in the horizontal direction.\nThis is used in combination with the nozzle size to define the number\nof perimeter lines and the thickness of those perimeter lines."))
setting('retraction_enable',        True, bool,  'machine',    _('Quality')).setLabel(_("Enable retraction"), _("Retract the filament when the nozzle is moving over a none-printed area. Details about the retraction can be configured in the advanced tab."))
setting('solid_layer_thickness',     0.6, float, 'basic',    _('Fill')).setRange(0).setLabel(_("Bottom/Top thickness (mm)"), _("This controls the thickness of the bottom and top layers, the amount of solid layers put down is calculated by the layer thickness and this value.\nHaving this value a multiple of the layer thickness makes sense. And keep it near your wall thickness to make an evenly strong part."))
setting('fill_density',               20, float, 'basic',    _('Fill')).setRange(0, 100).setLabel(_("Fill Density (%)"), _("This controls how densely filled the insides of your print will be. For a solid part use 100%, for an empty part use 0%. A value around 20% is usually enough.\nThis won't affect the outside of the print and only adjusts how strong the part becomes."))
setting('nozzle_size',               0.4, float, 'machine', _('Machine')).setRange(0.1,10).setLabel(_("Nozzle size (mm)"), _("The nozzle size is very important, this is used to calculate the line width of the infill, and used to calculate the amount of outside wall lines and thickness for the wall thickness you entered in the print settings."))
setting('print_speed',                50, float, 'basic',    _('Speed and Temperature')).setRange(1).setLabel(_("Print speed (mm/s)"), _("Speed at which printing happens. A well adjusted Ultimaker can reach 150mm/s, but for good quality prints you want to print slower. Printing speed depends on a lot of factors. So you will be experimenting with optimal settings for this."))
setting('print_temperature',         220, int,   'basic',    _('Speed and Temperature')).setRange(0,340).setLabel(_("Printing temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_temperature2',        220, int,   'basic',    _('Speed and Temperature')).setRange(0,340).setLabel(_("2nd nozzle temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_temperature3',          0, int,   'basic',    _('Speed and Temperature')).setRange(0,340).setLabel(_("3th nozzle temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_temperature4',          0, int,   'basic',    _('Speed and Temperature')).setRange(0,340).setLabel(_("4th nozzle temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_bed_temperature',      70, int,   'basic',    _('Speed and Temperature')).setRange(0,340).setLabel(_("Bed temperature (C)"), _("Temperature used for the heated printer bed. Set at 0 to pre-heat yourself."))
setting('support',                'None', [_('None'), _('Touching buildplate'), _('Everywhere')], 'basic', _('Support')).setLabel(_("Support type"), _("Type of support structure build.\n\"Touching buildplate\" is the most commonly used support setting.\n\nNone does not do any support.\nTouching buildplate only creates support where the support structure will touch the build platform.\nEverywhere creates support even on top of parts of the model."))
setting('platform_adhesion',      'None', [_('None'), _('Skirt'), _('Brim'), _('Raft')], 'basic', _('Support')).setLabel(_("Platform adhesion type"), _("Different options that help in preventing corners from lifting due to warping.\nBrim adds a single layer thick flat area around your object which is easy to cut off afterwards, and it is the recommended option.\nRaft adds a thick raster below the object and a thin interface between this and your object.\nThe skirt is a line drawn around the object at the first layer."))
setting('support_dual_extrusion',  'Both', [_('Both'), _('First extruder'), _('Second extruder')], 'basic', _('Support')).setLabel(_("Support dual extrusion"), _("Which extruder to use for support material, for break-away support you can use both extruders.\nBut if one of the materials is more expensive then the other you could select an extruder to use for support material. This causes more extruder switches.\nYou can also use the 2nd extruder for soluble support materials."))
setting('support_dual_extrusion_index', 0, int, 'preference', 'hidden')
setting('wipe_tower_volume',          65, float, 'expert',   _('Dual extrusion')).setLabel(_("Wipe&prime tower volume per layer (mm3)"), _("The amount of material put in the wipe/prime tower.\nThis is done in volume because in general you want to extrude a\ncertain amount of volume to get the extruder going, independent on the layer height.\nThis means that with thinner layers, your tower gets bigger."))
setting('wipe_tower_volume_index', 1, int, 'preference', 'hidden')
setting('wipe_tower_z_hop',        0.2, float, 'expert',   _('Dual extrusion')).setLabel(_("Wipe&prime tower z-hop"), _("The z-hop to apply before moving to the wipe/prime tower."))
setting('wipe_tower_shape',        'Square', [_('Crenel'), _('Donut'), _('Square'), _('Wall'), _('Rectangle')], 'expert',   _('Dual extrusion')).setLabel(_("Wipe&prime tower shape"), _("The shape of the wipe/prime tower."))
setting('wipe_tower_skirt_line_count', 6, float, 'expert',   _('Dual extrusion')).setLabel(_("Wipe&prime tower skirt line count"), _("Number of skirt lines of the wipe/prime tower."))
setting('ooze_shield',             False, bool,  'basic',    _('Dual extrusion')).setLabel(_("Ooze shield"), _("The ooze shield is a 1 line thick shell around the object which stands a few mm from the object.\nThis shield catches any oozing from the unused nozzle in dual-extrusion."))
setting('filament_diameter',        2.85, float, 'basic',    _('Filament')).setRange(1).setLabel(_("Diameter (mm)"), _("Diameter of your filament, as accurately as possible.\nIf you cannot measure this value you will have to calibrate it, a higher number means less extrusion, a smaller number generates more extrusion."))
setting('filament_diameter2',          0, float, 'basic',    _('Filament')).setRange(0).setLabel(_("Diameter2 (mm)"), _("Diameter of your filament for the 2nd nozzle. Use 0 to use the same diameter as for nozzle 1."))
setting('filament_diameter3',          0, float, 'basic',    _('Filament')).setRange(0).setLabel(_("Diameter3 (mm)"), _("Diameter of your filament for the 3th nozzle. Use 0 to use the same diameter as for nozzle 1."))
setting('filament_diameter4',          0, float, 'basic',    _('Filament')).setRange(0).setLabel(_("Diameter4 (mm)"), _("Diameter of your filament for the 4th nozzle. Use 0 to use the same diameter as for nozzle 1."))
setting('filament_flow',            100., float, 'basic',    _('Filament')).setRange(5,300).setLabel(_("Flow (%)"), _("Flow compensation, the amount of material extruded is multiplied by this value"))
setting('filament_flow2',            100., float, 'basic',    _('Filament')).setRange(5,300).setLabel(_("Flow (%)"), _("Flow compensation, the amount of material extruded is multiplied by this value"))
setting('retraction_speed',         40.0, float, 'advanced', _('Retraction')).setRange(0.1).setLabel(_("Speed (mm/s)"), _("Speed at which the filament is retracted, a higher retraction speed works better. But a very high retraction speed can lead to filament grinding."))
setting('retraction_amount',         4.5, float, 'advanced', _('Retraction')).setRange(0).setLabel(_("Distance (mm)"), _("Amount of retraction, set at 0 for no retraction at all. A value of 4.5mm seems to generate good results."))
setting('retraction_speed2',         40.0, float, 'advanced', _('Retraction')).setRange(0.1).setLabel(_("Speed (mm/s)"), _("Speed at which the filament is retracted, a higher retraction speed works better. But a very high retraction speed can lead to filament grinding."))
setting('retraction_amount2',         4.5, float, 'advanced', _('Retraction')).setRange(0).setLabel(_("Distance (mm)"), _("Amount of retraction, set at 0 for no retraction at all. A value of 4.5mm seems to generate good results."))
setting('retraction_dual_amount',   0.0, float, 'advanced', _('Retraction')).setRange(0).setLabel(_("Dual extrusion switch amount (mm)"), _("Amount of retraction when switching nozzle with dual-extrusion, set at 0 for no retraction at all. A value of 16.0mm seems to generate good results."))
setting('retraction_min_travel',     1.5, float, 'expert',   _('Retraction')).setRange(0).setLabel(_("Minimum travel (mm)"), _("Minimum amount of travel needed for a retraction to happen at all. To make sure you do not get a lot of retractions in a small area."))
setting('retraction_combing',      'All',  [_('Off'),_('All'),_('No Skin')], 'expert', _('Retraction')).setLabel(_("Enable combing"), _("Combing is the act of avoiding holes in the print for the head to travel over. If combing is \'Off\' the printer head moves straight from the start point to the end point and it will always retract.  If \'All\', enable combing on all surfaces.  If \'No Skin\', enable combing on all except skin surfaces."))
setting('retraction_minimal_extrusion',0.02, float,'expert', _('Retraction')).setRange(0).setLabel(_("Minimal extrusion before retracting (mm)"), _("The minimal amount of extrusion that needs to be done before retracting again if a retraction needs to happen before this minimal is reached the retraction is ignored.\nThis avoids retracting a lot on the same piece of filament which flattens the filament and causes grinding issues."))
setting('retraction_hop',            0.0, float, 'expert',   _('Retraction')).setRange(0).setLabel(_("Z hop when retracting (mm)"), _("When a retraction is done, the head is lifted by this amount to travel over the print. A value of 0.075 works well. This feature has a lot of positive effect on delta towers."))
setting('start_retraction_amount', 0.0, float, 'expert',   _('Retraction')).setRange(0).setLabel(_("Start retraction amount (mm)"), _("Generic retraction amount used in gcode start"))
setting('switch_default_retraction_amount', 0.0, float, 'expert',   _('Retraction')).setRange(0).setLabel(_("Switch default retraction amount (mm)"), _("Generic retraction amount used when switching extruder"))
setting('switch_default_retraction_offset', 0.0, float, 'expert',   _('Retraction')).setRange(0).setLabel(_("Switch default retraction offset (mm)"), _("Generic retraction offset used when switching extruder"))
setting('bottom_thickness',          0.3, float, 'advanced', _('Quality')).setRange(0).setLabel(_("Initial layer thickness (mm)"), _("Layer thickness of the bottom layer. A thicker bottom layer makes sticking to the bed easier. Set to 0.0 to have the bottom layer thickness the same as the other layers."))
setting('layer0_width_factor',       100, float, 'advanced', _('Quality')).setRange(50, 300).setLabel(_("Initial layer line width (%)"), _("Extra width factor for the extrusion on the first layer, on some printers it's good to have wider extrusion on the first layer to get better bed adhesion."))
setting('object_sink',               0.0, float, 'advanced', _('Quality')).setRange(0).setLabel(_("Cut off object bottom (mm)"), _("Sinks the object into the platform, this can be used for objects that do not have a flat bottom and thus create a too small first layer."))
#setting('enable_skin',             False, bool,  'advanced', _('Quality')).setLabel(_("Duplicate outlines"), _("Skin prints the outer lines of the prints twice, each time with half the thickness. This gives the illusion of a higher print quality."))
setting('overlap_dual',             0.15, float, 'advanced', _('Quality')).setLabel(_("Dual extrusion overlap (mm)"), _("Add a certain amount of overlapping extrusion on dual-extrusion prints. This bonds the different colors together."))
setting('travel_speed',            150.0, float, 'advanced', _('Speed')).setRange(0.1).setLabel(_("Travel speed (mm/s)"), _("Speed at which travel moves are done, a well built Ultimaker can reach speeds of 250mm/s. But some machines might miss steps then."))
setting('bottom_layer_speed',         20, float, 'advanced', _('Speed')).setRange(0.1).setLabel(_("Bottom layer speed (mm/s)"), _("Print speed for the bottom layer, you want to print the first layer slower so it sticks better to the printer bed."))
setting('infill_speed',              0.0, float, 'advanced', _('Speed')).setRange(0.0).setLabel(_("Infill speed (mm/s)"), _("Speed at which infill parts are printed. If set to 0 then the print speed is used for the infill. Printing the infill faster can greatly reduce printing time, but this can negatively affect print quality."))
setting('solidarea_speed',           0.0, float, 'advanced', _('Speed')).setRange(0.0).setLabel(_("Top/bottom speed (mm/s)"), _("Speed at which top/bottom parts are printed. If set to 0 then the print speed is used for the infill. Printing the top/bottom faster can greatly reduce printing time, but this can negatively affect print quality."))
setting('inset0_speed',              0.0, float, 'advanced', _('Speed')).setRange(0.0).setLabel(_("Outer shell speed (mm/s)"), _("Speed at which outer shell is printed. If set to 0 then the print speed is used. Printing the outer shell at a lower speed improves the final skin quality. However, having a large difference between the inner shell speed and the outer shell speed will effect quality in a negative way."))
setting('insetx_speed',              0.0, float, 'advanced', _('Speed')).setRange(0.0).setLabel(_("Inner shell speed (mm/s)"), _("Speed at which inner shells are printed. If set to 0 then the print speed is used. Printing the inner shell faster then the outer shell will reduce printing time. It is good to set this somewhere in between the outer shell speed and the infill/printing speed."))
setting('cool_min_layer_time',         5, float, 'advanced', _('Cool')).setRange(0).setLabel(_("Minimal layer time (sec)"), _("Minimum time spent in a layer, gives the layer time to cool down before the next layer is put on top. If the layer will be placed down too fast the printer will slow down to make sure it has spent at least this amount of seconds printing this layer."))
setting('fan_enabled',              True, bool,  'advanced', _('Cool')).setLabel(_("Enable cooling fan"), _("Enable the cooling fan during the print. The extra cooling from the cooling fan is essential during faster prints."))

setting('skirt_line_count',            2, int,   'expert', 'Skirt').setRange(0).setLabel(_("Line count"), _("The skirt is a line drawn around the object at the first layer. This helps to prime your extruder, and to see if the object fits on your platform.\nSetting this to 0 will disable the skirt. Multiple skirt lines can help priming your extruder better for small objects."))
setting('skirt_gap',                 3.0, float, 'expert', 'Skirt').setRange(0).setLabel(_("Start distance (mm)"), _("The distance between the skirt and the first layer.\nThis is the minimal distance, multiple skirt lines will be put outwards from this distance."))
setting('skirt_minimal_length',    150.0, float, 'expert', 'Skirt').setRange(0).setLabel(_("Minimal length (mm)"), _("The minimal length of the skirt, if this minimal length is not reached it will add more skirt lines to reach this minimal lenght.\nNote: If the line count is set to 0 this is ignored."))
setting('fan_full_height',           0.5, float, 'expert',   _('Cool')).setRange(0).setLabel(_("Fan full on at height (mm)"), _("The height at which the fan is turned on completely. For the layers below this the fan speed is scaled linearly with the fan off at layer 0."))
setting('fan_speed',                 20, int,   'expert',   _('Cool')).setRange(0,100).setLabel(_("Fan speed min (%)"), _("When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Minimal fan speed is used if the layer is not slowed down due to cooling."))
setting('fan_speed_max',             80, int,   'expert',   _('Cool')).setRange(0,100).setLabel(_("Fan speed max (%)"), _("When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Maximal fan speed is used if the layer is slowed down due to cooling by more than 200%."))
setting('cool_min_feedrate',          10, float, 'expert',   _('Cool')).setRange(0).setLabel(_("Minimum speed (mm/s)"), _("The minimal layer time can cause the print to slow down so much it starts to ooze. The minimal feedrate protects against this. Even if a print gets slowed down it will never be slower than this minimal speed."))
setting('cool_head_lift',          False, bool,  'expert',   _('Cool')).setLabel(_("Cool head lift"), _("Lift the head if the minimal speed is hit because of cool slowdown, and wait the extra time so the minimal layer time is always hit."))
setting('solid_top', True, bool, 'expert', _('Infill')).setLabel(_("Solid infill top"), _("Create a solid top surface, if set to false the top is filled with the fill percentage. Useful for cups/vases."))
setting('solid_bottom', True, bool, 'expert', _('Infill')).setLabel(_("Solid infill bottom"), _("Create a solid bottom surface, if set to false the bottom is filled with the fill percentage. Useful for buildings."))
setting('fill_overlap', 15, int, 'expert', _('Infill')).setRange(0,100).setLabel(_("Infill overlap (%)"), _("Amount of overlap between the infill and the walls. There is a slight overlap with the walls and the infill so the walls connect firmly to the infill."))
setting('perimeter_before_infill', True, bool, 'expert', _('Infill')).setLabel(_("Infill prints after perimeters"), _("Print infill after perimeter lines. This can reduce infill from showing through the surface. If not checked, infill will print before perimeter lines."))
setting('support_type', 'Grid', ['Grid', 'Lines'], 'expert', _('Support')).setLabel(_("Structure type"), _("The type of support structure.\nGrid is very strong and can come off in 1 piece, however, sometimes it is too strong.\nLines are single walled lines that break off one at a time. Which is more work to remove, but as it is less strong it does work better on tricky prints."))
setting('support_angle', 60, float, 'expert', _('Support')).setRange(0,90).setLabel(_("Overhang angle for support (deg)"), _("The minimal angle that overhangs need to have to get support. With 0 degree being horizontal and 90 degree being vertical."))
setting('support_fill_rate', 15, int, 'expert', _('Support')).setRange(0,100).setLabel(_("Fill amount (%)"), _("Amount of infill structure in the support material, less material gives weaker support which is easier to remove. 15% seems to be a good average."))
setting('support_xy_distance', 0.7, float, 'expert', _('Support')).setRange(0,10).setLabel(_("Distance X/Y (mm)"), _("Distance of the support material from the print, in the X/Y directions.\n0.7mm gives a nice distance from the print so the support does not stick to the print."))
setting('support_z_distance', 0.15, float, 'expert', _('Support')).setRange(0,10).setLabel(_("Distance Z (mm)"), _("Distance from the top/bottom of the support to the print. A small gap here makes it easier to remove the support but makes the print a bit uglier.\n0.15mm gives a good seperation of the support material."))
setting('spiralize', False, bool, 'expert', 'Black Magic').setLabel(_("Spiralize the outer contour"), _("Spiralize is smoothing out the Z move of the outer edge. This will create a steady Z increase over the whole print. This feature turns a solid object into a single walled print with a solid bottom.\nThis feature used to be called Joris in older versions."))
setting('simple_mode', False, bool, 'expert', 'Black Magic').setLabel(_("Only follow mesh surface"), _("Only follow the mesh surfaces of the 3D model, do not do anything else. No infill, no top/bottom, nothing."))
#setting('bridge_speed', 100, int, 'expert', 'Bridge').setRange(0,100).setLabel(_("Bridge speed (%)"), _("Speed at which layers with bridges are printed, compared to normal printing speed."))
setting('brim_line_count', 20, int, 'expert', _('Brim')).setRange(1,100).setLabel(_("Brim line amount"), _("The amount of lines used for a brim, more lines means a larger brim which sticks better, but this also makes your effective print area smaller."))
setting('raft_margin', 5.0, float, 'expert', _('Raft')).setRange(0).setLabel(_("Extra margin (mm)"), _("If the raft is enabled, this is the extra raft area around the object which is also rafted. Increasing this margin will create a stronger raft while using more material and leaving less area for your print."))
setting('raft_line_spacing', 3.0, float, 'expert', _('Raft')).setRange(0).setLabel(_("Line spacing (mm)"), _("When you are using the raft this is the distance between the centerlines of the raft line."))
setting('raft_base_thickness', 0.3, float, 'expert', _('Raft')).setRange(0).setLabel(_("Base thickness (mm)"), _("When you are using the raft this is the thickness of the base layer which is put down."))
setting('raft_base_linewidth', 1.0, float, 'expert', _('Raft')).setRange(0).setLabel(_("Base line width (mm)"), _("When you are using the raft this is the width of the base layer lines which are put down."))
setting('raft_interface_thickness', 0.27, float, 'expert', _('Raft')).setRange(0).setLabel(_("Interface thickness (mm)"), _("When you are using the raft this is the thickness of the interface layer which is put down."))
setting('raft_interface_linewidth', 0.4, float, 'expert', _('Raft')).setRange(0).setLabel(_("Interface line width (mm)"), _("When you are using the raft this is the width of the interface layer lines which are put down."))
setting('raft_airgap_all', 0.0, float, 'expert', _('Raft')).setRange(0).setLabel(_("Airgap"), _("Gap between the last layer of the raft the whole print."))
setting('raft_airgap', 0.22, float, 'expert', _('Raft')).setRange(0).setLabel(_("First Layer Airgap"), _("Gap between the last layer of the raft and the first printing layer. A small gap of 0.2mm works wonders on PLA and makes the raft easy to remove. This value is added on top of the 'Airgap' setting."))
setting('raft_surface_layers', 2, int, 'expert', _('Raft')).setRange(0).setLabel(_("Surface layers"), _("Amount of surface layers put on top of the raft, these are fully filled layers on which the model is printed."))
setting('raft_surface_thickness', 0.27, float, 'expert', _('Raft')).setRange(0).setLabel(_("Surface layer thickness (mm)"), _("Thickness of each surface layer."))
setting('raft_surface_linewidth', 0.4, float, 'expert', _('Raft')).setRange(0).setLabel(_("Surface layer line width (mm)"), _("Width of the lines for each surface layer."))
setting('fix_horrible_union_all_type_a', True,  bool, 'expert', _('Fix horrible')).setLabel(_("Combine everything (Type-A)"), _("This expert option adds all parts of the model together. The result is usually that internal cavities disappear. Depending on the model this can be intended or not. Enabling this option is at your own risk. Type-A is dependent on the model normals and tries to keep some internal holes intact. Type-B ignores all internal holes and only keeps the outside shape per layer."))
setting('fix_horrible_union_all_type_b', False, bool, 'expert', _('Fix horrible')).setLabel(_("Combine everything (Type-B)"), _("This expert option adds all parts of the model together. The result is usually that internal cavities disappear. Depending on the model this can be intended or not. Enabling this option is at your own risk. Type-A is dependent on the model normals and tries to keep some internal holes intact. Type-B ignores all internal holes and only keeps the outside shape per layer."))
setting('fix_horrible_use_open_bits', False, bool, 'expert', _('Fix horrible')).setLabel(_("Keep open faces"), _("This expert option keeps all the open bits of the model intact. Normally Cura tries to stitch up small holes and remove everything with big holes, but this option keeps bits that are not properly part of anything and just goes with whatever is left. This option is usually not what you want, but it might enable you to slice models otherwise failing to produce proper paths.\nAs with all \"Fix horrible\" options, results may vary and use at your own risk."))
setting('fix_horrible_extensive_stitching', False, bool, 'expert', _('Fix horrible')).setLabel(_("Extensive stitching"), _("Extensive stitching tries to fix up open holes in the model by closing the hole with touching polygons. This algorthm is quite expensive and could introduce a lot of processing time.\nAs with all \"Fix horrible\" options, results may vary and use at your own risk."))

setting('start_extruder', 0, int, 'hidden', 'hidden')
setting('print_duration', '', str, 'hidden', 'hidden')
setting('filament_length', '', str, 'hidden', 'hidden')
setting('filament_weight', '', str, 'hidden', 'hidden')
setting('filament_cost', '', str, 'hidden', 'hidden')
setting('filament2_length', '', str, 'hidden', 'hidden')
setting('filament2_weight', '', str, 'hidden', 'hidden')
setting('filament2_cost', '', str, 'hidden', 'hidden')
setting('plugin_config', '', str, 'hidden', 'hidden')
setting('object_center_x', -1, float, 'hidden', 'hidden')
setting('object_center_y', -1, float, 'hidden', 'hidden')
setting('start.gcode', '', str, 'alteration', 'alteration')
setting('end.gcode',  '', str, 'alteration', 'alteration')
setting('preSwitchExtruder.gcode', '', str, 'alteration', 'alteration')
setting('postSwitchExtruder.gcode', '', str, 'alteration', 'alteration')
setting('preSwitchExtruder2.gcode', '', str, 'alteration', 'alteration')
setting('postSwitchExtruder2.gcode', '', str, 'alteration', 'alteration')
setting('startMode', 'Normal', ['Simple', 'Normal'], 'preference', 'hidden')
setting('oneAtATime', 'False', bool, 'preference', 'hidden')
setting('lastFile', os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'resources', 'example', 'dagoma.stl')), str, 'preference', 'hidden')
setting('save_profile', 'False', bool, 'preference', 'hidden').setLabel(_("Save profile on slice"), _("When slicing save the profile as [stl_file]_profile.ini next to the model."))
setting('filament_cost_kg', '46', float, 'advanced', _('Filament')).setLabel(_("Cost (price/kg)"), _("Cost of your filament per kg, to estimate the cost of the final print."))
setting('filament_cost_kg2', '46', float, 'advanced', _('Filament')).setLabel(_("Cost (price/kg)"), _("Cost of your filament per kg, to estimate the cost of the final print."))
setting('filament_cost_meter', '0', float, 'advanced', _('Filament')).setLabel(_("Cost (price/m)"), _("Cost of your filament per meter, to estimate the cost of the final print."))
setting('filament_cost_meter2', '0', float, 'advanced', _('Filament')).setLabel(_("Cost (price/m)"), _("Cost of your filament per meter, to estimate the cost of the final print."))
setting('auto_detect_sd', 'True', bool, 'advanced', 'hidden').setLabel(_("Auto detect SD card drive"), _("Auto detect the SD card. You can disable this because on some systems external hard-drives or USB sticks are detected as SD card."))
setting('check_for_updates', 'False', bool, 'preference', 'hidden').setLabel(_("Check for updates"), _("Check for newer versions of Cura on startup"))
setting('submit_slice_information', 'False', bool, 'preference', 'hidden').setLabel(_("Send usage statistics"), _("Submit anonymous usage information to improve future versions of Cura"))
setting('filament_index', 0, int, 'preference', 'hidden')
setting('filament_name', '', str, 'preference', 'hidden')
setting('filament2_index', 0, int, 'preference', 'hidden')
setting('filament2_name', '', str, 'preference', 'hidden')
setting('xml_file', '', str, 'preference', 'hidden')
setting('color_label', 'Generic', str, 'preference', 'hidden')
setting('color2_label', 'Generic', str, 'preference', 'hidden')
setting('fill_index', 2, int, 'preference', 'hidden')
setting('precision_index', 0, int, 'preference', 'hidden')
setting('filament_physical_density', '1270', float, 'advanced', _('Filament')).setRange(500.0, 3000.0).setLabel(_("Density (kg/m3)"), _("Weight of the filament per m3. Around 1240 for PLA. And around 1040 for ABS. This value is used to estimate the weight if the filament used for the print."))
setting('filament_physical_density2', '1270', float, 'advanced', _('Filament')).setRange(500.0, 3000.0).setLabel(_("Density (kg/m3)"), _("Weight of the filament per m3. Around 1240 for PLA. And around 1040 for ABS. This value is used to estimate the weight if the filament used for the print."))

# Get the os default locale
default_locale = "en_US"
if platform.system() == "Darwin":
	import subprocess
	default_locale = subprocess.getoutput("defaults read -g AppleLocale")
else:
	import locale
	default_locale = locale.getdefaultlocale()[0]

# Set the default language from the found default locale
default_language = 'English'
if not default_locale.find('fr') == -1:
	default_language = 'French'

setting('language', default_language, str, 'preference', 'hidden').setLabel(_('Language'), _('Change the language in which Cura runs. Switching language requires a restart of Cura'))
setting('active_machine', '0', int, 'preference', 'hidden')

setting('model_colour', '#FF9B00', str, 'preference', 'hidden').setLabel(_('Model colour'), _('Display color for first extruder'))
setting('model_colour2', '#CB3030', str, 'preference', 'hidden').setLabel(_('Model colour (2)'), _('Display color for second extruder'))
setting('model_colour3', '#DDD93C', str, 'preference', 'hidden').setLabel(_('Model colour (3)'), _('Display color for third extruder'))
setting('model_colour4', '#4550D3', str, 'preference', 'hidden').setLabel(_('Model colour (4)'), _('Display color for forth extruder'))
setting('printing_window', 'Basic', ['Basic'], 'preference', 'hidden').setLabel(_('Printing window type'), _('Select the interface used for USB printing.'))

setting('window_normal_sash', -310, int, 'preference', 'hidden')
setting('minimum_pane_size', 310, int, 'preference', 'hidden')
setting('last_run_version', '', str, 'preference', 'hidden')

setting('machine_name', '', str, 'machine', 'hidden')
setting('machine_type', 'unknown', str, 'machine', 'hidden') #Ultimaker, Ultimaker2, RepRap
setting('machine_width', '205', float, 'machine', 'hidden').setLabel(_("Maximum width (mm)"), _("Size of the machine in mm"))
setting('machine_depth', '205', float, 'machine', 'hidden').setLabel(_("Maximum depth (mm)"), _("Size of the machine in mm"))
setting('machine_height', '200', float, 'machine', 'hidden').setLabel(_("Maximum height (mm)"), _("Size of the machine in mm"))
setting('machine_center_is_zero', 'False', bool, 'machine', 'hidden').setLabel(_("Machine center 0,0"), _("Machines firmware defines the center of the bed as 0,0 instead of the front left corner."))
setting('machine_shape', 'Square', ['Square','Circular'], 'machine', 'hidden').setLabel(_("Build area shape"), _("The shape of machine build area."))
setting('machine_speed_factor', '1.0', float, 'machine', 'hidden')
setting('has_heated_bed', 'False', bool, 'machine', 'hidden').setLabel(_("Heated bed"), _("If you have an heated bed, this enabled heated bed settings (requires restart)"))
setting('gcode_flavor', 'RepRap (Marlin/Sprinter)', ['RepRap (Marlin/Sprinter)', 'RepRap (Volumetric)', 'UltiGCode', 'MakerBot', 'BFB', 'Mach3'], 'machine', 'hidden').setLabel(_("GCode Flavor"), _("Flavor of generated GCode.\nRepRap is normal 5D GCode which works on Marlin/Sprinter based firmwares.\nUltiGCode is a variation of the RepRap GCode which puts more settings in the machine instead of the slicer.\nMakerBot GCode has a few changes in the way GCode is generated, but still requires MakerWare to generate to X3G.\nBFB style generates RPM based code.\nMach3 uses A,B,C instead of E for extruders."))
setting('extruder_amount', '1', ['1','2','3','4','5'], 'machine', 'hidden').setLabel(_("Extruder count"), _("Amount of extruders in your machine."))
setting('extruder_offset_x1', '0.0', float, 'machine', 'hidden').setLabel(_("Offset X"), _("The offset of your secondary extruder compared to the primary."))
setting('extruder_offset_y1', '0.0', float, 'machine', 'hidden').setLabel(_("Offset Y"), _("The offset of your secondary extruder compared to the primary."))
setting('extruder_offset_x2', '0.0', float, 'machine', 'hidden').setLabel(_("Offset X"), _("The offset of your tertiary extruder compared to the primary."))
setting('extruder_offset_y2', '0.0', float, 'machine', 'hidden').setLabel(_("Offset Y"), _("The offset of your tertiary extruder compared to the primary."))
setting('extruder_offset_x3', '0.0', float, 'machine', 'hidden').setLabel(_("Offset X"), _("The offset of your forth extruder compared to the primary."))
setting('extruder_offset_y3', '0.0', float, 'machine', 'hidden').setLabel(_("Offset Y"), _("The offset of your forth extruder compared to the primary."))
setting('steps_per_e', '0', float, 'machine', 'hidden').setLabel(_("E-Steps per 1mm filament"), _("Amount of steps per mm filament extrusion. If set to 0 then this value is ignored and the value in your firmware is used."))
setting('serial_port', 'AUTO', str, 'machine', 'hidden').setLabel(_("Serial port"), _("Serial port to use for communication with the printer"))
setting('serial_port_auto', '', str, 'machine', 'hidden')
setting('serial_baud', 'AUTO', str, 'machine', 'hidden').setLabel(_("Baudrate"), _("Speed of the serial port communication\nNeeds to match your firmware settings\nCommon values are 250000, 115200, 57600"))
setting('serial_baud_auto', '', int, 'machine', 'hidden')

setting('extruder_head_size_min_x', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards X min (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 75mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_min_y', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards Y min (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 18mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_max_x', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards X max (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 18mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_max_y', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards Y max (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 35mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_height', '0.0', float, 'machine', 'hidden').setLabel(_("Printer gantry height (mm)"), _("The height of the gantry holding up the printer head. If an object is higher then this then you cannot print multiple objects one for one. 60mm for an Ultimaker."))

setting('min_segment_length', '10', int, 'machine', 'hidden').setLabel(_("Minimum segment length in microns"), _("."))
setting('machine_acceleration', '3000.0', float, 'machine', 'hidden').setLabel(_("Acceleration"), _("."))
setting('machine_max_acceleration[0]', '9000.0', float, 'machine', 'hidden').setLabel(_("Max acceleration X"), _("."))
setting('machine_max_acceleration[1]', '9000.0', float, 'machine', 'hidden').setLabel(_("Max acceleration Y"), _("."))
setting('machine_max_acceleration[2]', '100.0', float, 'machine', 'hidden').setLabel(_("Max acceleration Z"), _("."))
setting('machine_max_acceleration[3]', '10000.0', float, 'machine', 'hidden').setLabel(_("Max acceleration E"), _("."))
setting('machine_max_xy_jerk', '20.0', float, 'machine', 'hidden').setLabel(_("XY \"Jerk\""), _("."))
setting('machine_max_z_jerk', '0.4', float, 'machine', 'hidden').setLabel(_("Z \"Jerk\""), _("."))
setting('machine_max_e_jerk', '5.0', float, 'machine', 'hidden').setLabel(_("E \"Jerk\""), _("."))

setting('printing_surface_name', '', str, 'printing_surface', _('PrintingSurface')).setLabel(_("Printing surface name"), _("Printing surface name."))
setting('printing_surface_name_index', 0, int, 'preference', 'hidden')
setting('printing_surface_height', 0.0, float, 'printing_surface', _('PrintingSurface')).setRange(0.0001).setLabel(_("Printing surface height (mm)"), _("Printing surface height."))

setting('offset_value', 0.0, float, 'advanced', _('Offset')).setRange(0.0001).setLabel(_("Offset value (mm)"), _("Calculated offset value."))
setting('offset_input', 0.0, float, 'advanced', _('Offset')).setRange(0.0001).setLabel(_("Offset value (mm)"), _("Input offset value."))
setting('sensor', 'Sensor', str, 'advanced', _('Sensor')).setLabel(_("Enabled the sensor"), _("To check if you want to use the sensor."))

setting('show_magis_options', 'False', bool, 'preference', 'hidden')

validators.warningAbove(settingsDictionary['filament_flow'], 150, _("More flow than 150% is rare and usually not recommended."))
validators.warningBelow(settingsDictionary['filament_flow'], 50, _("Less flow than 50% is rare and usually not recommended."))
validators.warningAbove(settingsDictionary['layer_height'], lambda : (float(getMachineSetting('nozzle_size')) * 80.0 / 100.0), _("Thicker layers then %.2fmm (80%% nozzle size) usually give bad results and are not recommended."))
validators.wallThicknessValidator(settingsDictionary['wall_thickness'])
validators.warningAbove(settingsDictionary['print_speed'], 150.0, _("It is highly unlikely that your machine can achieve a printing speed above 150mm/s"))
validators.printSpeedValidator(settingsDictionary['print_speed'])
validators.warningAbove(settingsDictionary['print_temperature'], 260.0, _("Temperatures above 260C could damage your machine, be careful!"))
validators.warningAbove(settingsDictionary['print_temperature2'], 260.0, _("Temperatures above 260C could damage your machine, be careful!"))
validators.warningAbove(settingsDictionary['print_temperature3'], 260.0, _("Temperatures above 260C could damage your machine, be careful!"))
validators.warningAbove(settingsDictionary['print_temperature4'], 260.0, _("Temperatures above 260C could damage your machine, be careful!"))
validators.warningAbove(settingsDictionary['filament_diameter'], 3.5, _("Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm."))
validators.warningAbove(settingsDictionary['filament_diameter2'], 3.5, _("Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm."))
validators.warningAbove(settingsDictionary['filament_diameter3'], 3.5, _("Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm."))
validators.warningAbove(settingsDictionary['filament_diameter4'], 3.5, _("Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm."))
validators.warningAbove(settingsDictionary['travel_speed'], 300.0, _("It is highly unlikely that your machine can achieve a travel speed above 300mm/s"))
validators.warningAbove(settingsDictionary['bottom_thickness'], lambda : (float(getMachineSetting('nozzle_size')) * 3.0 / 4.0), _("A bottom layer of more then %.2fmm (3/4 nozzle size) usually give bad results and is not recommended."))

#Conditions for multiple extruders
settingsDictionary['print_temperature2'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['print_temperature3'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 2)
settingsDictionary['print_temperature4'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 3)
settingsDictionary['filament_diameter2'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['filament_diameter3'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 2)
settingsDictionary['filament_diameter4'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 3)
settingsDictionary['support_dual_extrusion'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['retraction_dual_amount'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['wipe_tower_volume'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['ooze_shield'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
#Heated bed
settingsDictionary['print_bed_temperature'].addCondition(lambda : getMachineSetting('has_heated_bed') == 'True')

#UltiGCode uses less settings, as these settings are located inside the machine instead of gcode.
settingsDictionary['print_temperature'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_temperature2'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_temperature3'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_temperature4'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter2'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter3'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter4'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_flow'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_bed_temperature'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['retraction_speed'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['retraction_amount'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['retraction_dual_amount'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')

#Remove fake defined _() because later the localization will define a global _()
del _

#########################################################
## Profile and preferences functions
#########################################################

def getSubCategoriesFor(category):
	done = {}
	ret = []
	for s in settingsList:
		if s.getCategory() == category and not s.getSubCategory() in done and s.checkConditions():
			done[s.getSubCategory()] = True
			ret.append(s.getSubCategory())
	return ret

def getSettingsForCategory(category, subCategory = None):
	ret = []
	for s in settingsList:
		if s.getCategory() == category and (subCategory is None or s.getSubCategory() == subCategory) and s.checkConditions():
			ret.append(s)
	return ret

## Profile functions
def getBasePath():
	"""
	:return: The path in which the current configuration files are stored. This depends on the used OS.
	"""
	if platform.system() == "Windows":
		basePath = os.path.normpath(os.path.expanduser('~/.curaByDagoma/' + os.environ['CURABYDAGO_VERSION']))
	elif platform.system() == "Darwin":
		basePath = os.path.expanduser('~/Library/Application Support/CuraByDagoma/' + os.environ['CURABYDAGO_VERSION'])
	else:
		basePath = os.path.expanduser('~/.curaByDagoma/' + os.environ['CURABYDAGO_VERSION'])
	if not os.path.isdir(basePath):
		try:
			os.makedirs(basePath)
		except:
			print("Failed to create directory: %s" % (basePath))
	return basePath

def getAlternativeBasePaths():
	"""
	Search for alternative installations of Cura and their preference files. Used to load configuration from older versions of Cura.
	"""
	paths = []
	basePath = os.path.normpath(os.path.join(getBasePath(), '..'))
	for subPath in os.listdir(basePath):
		path = os.path.join(basePath, subPath)
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'preferences.ini')) and path != getBasePath():
			paths.append(path)
		path = os.path.join(basePath, subPath, 'Cura')
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'preferences.ini')) and path != getBasePath():
			paths.append(path)

	#Check the old base path, which was in the application directory.
	oldBasePath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
	basePath = os.path.normpath(os.path.join(oldBasePath, ".."))
	for subPath in os.listdir(basePath):
		path = os.path.join(basePath, subPath)
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'preferences.ini')) and path != oldBasePath:
			paths.append(path)
		path = os.path.join(basePath, subPath, 'Cura')
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'preferences.ini')) and path != oldBasePath:
			paths.append(path)

	return paths

def getDefaultProfilePath():
	"""
	:return: The default path where the currently used profile is stored and loaded on open and close of Cura.
	"""
	return os.path.join(getBasePath(), 'current_profile.ini')

def loadProfile(filename, allMachines = False):
	"""
		Read a profile file as active profile settings.
	:param filename:    The ini filename to save the profile in.
	:param allMachines: When False only the current active profile is saved. If True all profiles for all machines are saved.
	"""
	global settingsList
	profileParser = ConfigParser.ConfigParser()
	try:
		profileParser.read(filename, encoding='utf-8')
	except ConfigParser.ParsingError:
		return
	if allMachines:
		n = 0
		while profileParser.has_section('profile_%d' % (n)):
			for set in settingsList:
				if set.isPreference():
					continue
				section = 'profile_%d' % (n)
				if set.isAlteration():
					section = 'alterations_%d' % (n)
				if profileParser.has_option(section, set.getName()):
					set.setValue(profileParser.get(section, set.getName()), n)
			n += 1
	else:
		for set in settingsList:
			if set.isPreference():
				continue
			section = 'profile'
			if set.isAlteration():
				section = 'alterations'
			if profileParser.has_option(section, set.getName()):
				set.setValue(profileParser.get(section, set.getName()))

def saveProfile(filename, allMachines = False):
	"""
		Save the current profile to an ini file.
	:param filename:    The ini filename to save the profile in.
	:param allMachines: When False only the current active profile is saved. If True all profiles for all machines are saved.
	"""
	global settingsList
	profileParser = ConfigParser.ConfigParser()
	if allMachines:
		for set in settingsList:
			if set.isPreference() or set.isMachineSetting():
				continue
			for n in range(0, getMachineCount()):
				if set.isAlteration():
					section = 'alterations_%d' % (n)
				else:
					section = 'profile_%d' % (n)
				if not profileParser.has_section(section):
					profileParser.add_section(section)
				profileParser.set(section, set.getName(), set.getValue(n))
	else:
		profileParser.add_section('profile')
		profileParser.add_section('alterations')
		for set in settingsList:
			if set.isPreference() or set.isMachineSetting():
				continue
			if set.isAlteration():
				profileParser.set('alterations', set.getName(), set.getValue())
			else:
				profileParser.set('profile', set.getName(), set.getValue())

	try:
		profileParser.write(open(filename, 'w', encoding='utf-8'))
	except:
		print("Failed to write profile file: %s" % (filename))

def resetProfile():
	""" Reset the profile for the current machine to default. """
	global settingsList
	for set in settingsList:
		if not set.isProfile():
			continue
		set.setValue(set.getDefault())

	if getMachineSetting('machine_type') == 'ultimaker':
		putMachineSetting('nozzle_size', '0.4')
		putMachineSetting('retraction_enable', 'True')
	elif getMachineSetting('machine_type') == 'ultimaker2':
		putMachineSetting('nozzle_size', '0.4')
		putMachineSetting('retraction_enable', 'True')
	else:
		putMachineSetting('nozzle_size', '0.4')
		putMachineSetting('retraction_enable', 'True')

def setProfileFromString(options):
	"""
	Parse an encoded string which has all the profile settings stored inside of it.
	Used in combination with getProfileString to ease sharing of profiles.
	"""
	options = base64.b64decode(options)
	options = zlib.decompress(options)
	(profileOpts, alt) = options.split('\f', 1)
	global settingsDictionary
	for option in profileOpts.split('\b'):
		if len(option) > 0:
			(key, value) = option.split('=', 1)
			if key in settingsDictionary:
				if settingsDictionary[key].isProfile():
					settingsDictionary[key].setValue(value)
	for option in alt.split('\b'):
		if len(option) > 0:
			(key, value) = option.split('=', 1)
			if key in settingsDictionary:
				if settingsDictionary[key].isAlteration():
					settingsDictionary[key].setValue(value)

def getProfileString():
	"""
	Get an encoded string which contains all profile settings.
	Used in combination with setProfileFromString to share settings in files, forums or other text based ways.
	"""
	p = []
	alt = []
	global settingsList
	for set in settingsList:
		if set.isProfile():
			if set.getName() in tempOverride:
				p.append(set.getName() + "=" + tempOverride[set.getName()])
			else:
				p.append(set.getName() + "=" + set.getValue())
		elif set.isAlteration():
			if set.getName() in tempOverride:
				alt.append(set.getName() + "=" + tempOverride[set.getName()])
			else:
				alt.append(set.getName() + "=" + set.getValue())
	ret = '\b'.join(p) + '\f' + '\b'.join(alt)
	ret = base64.b64encode(zlib.compress(bytes(ret, 'utf-8'), 9))
	return ret

def insertNewlines(string, every=64): #This should be moved to a better place then profile.
	lines = []
	for i in range(0, len(string), every):
		lines.append(string[i:i+every])
	return '\n'.join(lines)

def getPreferencesString():
	"""
	:return: An encoded string which contains all the current preferences.
	"""
	p = []
	global settingsList
	for set in settingsList:
		if set.isPreference():
			p.append(set.getName() + "=" + set.getValue())
	ret = '\b'.join(p)
	ret = base64.b64encode(zlib.compress(bytes(ret, 'utf-8'), 9))
	return ret


def getProfileSetting(name):
	"""
		Get the value of an profile setting.
	:param name: Name of the setting to retrieve.
	:return:     Value of the current setting.
	"""
	if name in tempOverride:
		return tempOverride[name]
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isProfile():
		return settingsDictionary[name].getValue()
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in profile settings\n' % (name))
	return ''

def getProfileSettingFloat(name):
	try:
		setting = getProfileSetting(name).replace(',', '.')
		return float(eval(setting, {}, {}))
	except:
		return 0.0

def putProfileSetting(name, value):
	""" Store a certain value in a profile setting. """
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isProfile():
		settingsDictionary[name].setValue(value)

def putAlterationSetting(name, value):
	""" Store a certain value in a alteration setting. """
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isAlteration():
		settingsDictionary[name].setValue(value)

def isProfileSetting(name):
	""" Check if a certain key name is actually a profile value. """
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isProfile():
		return True
	return False

## Preferences functions
def getPreferencePath():
	"""
	:return: The full path of the preference ini file.
	"""
	return os.path.join(getBasePath(), 'preferences.ini')

def getPreferenceFloat(name):
	"""
	Get the float value of a preference, returns 0.0 if the preference is not a invalid float
	"""
	try:
		setting = getPreference(name).replace(',', '.')
		return float(eval(setting, {}, {}))
	except:
		return 0.0

def getPreferenceInt(name):
	"""
	Get the int value of a preference, returns 0.0 if the preference is not a invalid float
	"""
	try:
		setting = getPreference(name).replace(',', '.')
		return int(eval(setting, {}, {}))
	except:
		return 0

def getPreferenceBool(name):
	"""
	Get the bool value of a preference, returns True if the preference is 'True', False otherwise
	"""
	setting = getPreference(name)
	if setting == 'True' or setting == 'true':
		return True
	return False

def getPreferenceColour(name):
	"""
	Get a preference setting value as a color array. The color is stored as #RRGGBB hex string in the setting.
	"""
	colorString = getPreference(name)
	return [float(int(colorString[1:3], 16)) / 255, float(int(colorString[3:5], 16)) / 255, float(int(colorString[5:7], 16)) / 255, 1.0]

def loadPreferences(filename):
	"""
	Read a configuration file as global config
	"""
	global settingsList
	profileParser = ConfigParser.ConfigParser()
	try:
		profileParser.read(filename)
	except ConfigParser.ParsingError:
		return

	for set in settingsList:
		if set.isPreference():
			if profileParser.has_option('preference', set.getName()):
				set.setValue(profileParser.get('preference', set.getName()))

	n = 0
	while profileParser.has_section('machine_%d' % (n)):
		for set in settingsList:
			if set.isMachineSetting():
				if profileParser.has_option('machine_%d' % (n), set.getName()):
					set.setValue(profileParser.get('machine_%d' % (n), set.getName()), n)
		n += 1

	setActiveMachine(int(getPreferenceFloat('active_machine')))

def loadMachineSettings(filename):
	global settingsList
	#Read a configuration file as global config
	profileParser = ConfigParser.ConfigParser()
	try:
		profileParser.read(filename)
	except ConfigParser.ParsingError:
		return

	for set in settingsList:
		if set.isMachineSetting():
			if profileParser.has_option('machine', set.getName()):
				set.setValue(profileParser.get('machine', set.getName()))
	checkAndUpdateMachineName()

def savePreferences(filename):
	global settingsList
	#Save the current profile to an ini file
	parser = ConfigParser.ConfigParser()
	parser.add_section('preference')

	for set in settingsList:
		if set.isPreference():
			parser.set('preference', set.getName(), set.getValue())

	n = 0
	while getMachineSetting('machine_name', n) != '':
		parser.add_section('machine_%d' % (n))
		for set in settingsList:
			if set.isMachineSetting():
				parser.set('machine_%d' % (n), set.getName(), set.getValue(n))
		n += 1
	try:
		parser.write(open(filename, 'w'))
	except:
		print("Failed to write preferences file: %s" % (filename))

def getPreference(name):
	if name in tempOverride:
		return tempOverride[name]
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isPreference():
		return settingsDictionary[name].getValue()
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in preferences\n' % (name))
	return ''

def putPreference(name, value):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isPreference():
		settingsDictionary[name].setValue(value)
		savePreferences(getPreferencePath())
		return
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in preferences\n' % (name))

def isPreference(name):
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isPreference():
		return True
	return False

def getMachineSettingFloat(name, index = None):
	try:
		setting = getMachineSetting(name, index).replace(',', '.')
		return float(eval(setting, {}, {}))
	except:
		return 0.0

def getMachineSettingInt(name, index = None):
	try:
		setting = getMachineSetting(name, index).replace(',', '.')
		return int(eval(setting, {}, {}))
	except:
		return -1

def getMachineSettingBool(name, index = None):
	try:
		setting = getMachineSetting(name, index).replace(',', '.')
		return bool(eval(setting, {}, {}))
	except:
		return False

def getMachineSetting(name, index = None):
	if name in tempOverride:
		return tempOverride[name]
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isMachineSetting():
		return settingsDictionary[name].getValue(index)
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in machine settings\n' % (name))
	return ''

def putMachineSetting(name, value, index = None):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isMachineSetting():
		settingsDictionary[name].setValue(value, index)
	savePreferences(getPreferencePath())

def isMachineSetting(name):
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isMachineSetting():
		return True
	return False

def checkAndUpdateMachineName():
	global _selectedMachineIndex
	name = getMachineSetting('machine_name')
	index = None
	if name == '':
		name = getMachineSetting('machine_type')
	for n in range(0, getMachineCount()):
		if n == _selectedMachineIndex:
			continue
		if index is None:
			if name == getMachineSetting('machine_name', n):
				index = 1
		else:
			if '%s (%d)' % (name, index) == getMachineSetting('machine_name', n):
				index += 1
	if index is not None:
		name = '%s (%d)' % (name, index)
	putMachineSetting('machine_name', name)
	putPreference('active_machine', _selectedMachineIndex)

def getMachineCount():
	n = 0
	while getMachineSetting('machine_name', n) != '':
		n += 1
	if n < 1:
		return 1
	return n

def setActiveMachine(index):
	global _selectedMachineIndex
	_selectedMachineIndex = index
	putPreference('active_machine', _selectedMachineIndex)

def removeMachine(index):
	global _selectedMachineIndex
	global settingsList
	if getMachineCount() < 2:
		return
	for n in range(index, getMachineCount()):
		for setting in settingsList:
			if setting.isMachineSetting():
				setting.setValue(setting.getValue(n+1), n)

	if _selectedMachineIndex >= index:
		setActiveMachine(getMachineCount() - 1)

## Temp overrides for multi-extruder slicing and the project planner.
tempOverride = {}
def setTempOverride(name, value):
	tempOverride[name] = str(value)
def clearTempOverride(name):
	del tempOverride[name]
def resetTempOverride():
	tempOverride.clear()

#########################################################
## Utility functions to calculate common profile values
#########################################################
def calculateEdgeWidth():
	wallThickness = getProfileSettingFloat('wall_thickness')
	nozzleSize = getMachineSettingFloat('nozzle_size')

	#if getProfileSetting('spiralize') == 'True' or getProfileSetting('simple_mode') == 'True':
	#	return wallThickness

	if wallThickness < 0.01:
		return nozzleSize
	if wallThickness < nozzleSize:
		return wallThickness

	lineCount = int(wallThickness / (nozzleSize - 0.0001))
	if lineCount == 0:
		return nozzleSize
	lineWidth = wallThickness / lineCount
	lineWidthAlt = wallThickness / (lineCount + 1)
	if lineWidth > nozzleSize * 1.5:
		return lineWidthAlt
	return lineWidth

def calculateLineCount():
	wallThickness = getProfileSettingFloat('wall_thickness')
	nozzleSize = getMachineSettingFloat('nozzle_size')

	if wallThickness < 0.01:
		return 0
	if wallThickness < nozzleSize:
		return 1
	if getProfileSetting('spiralize') == 'True' or getProfileSetting('simple_mode') == 'True':
		return 1

	lineCount = int(wallThickness / (nozzleSize - 0.0001))
	if lineCount < 1:
		lineCount = 1
	lineWidth = wallThickness / lineCount
	lineWidthAlt = wallThickness / (lineCount + 1)
	if lineWidth > nozzleSize * 1.5:
		return lineCount + 1
	return lineCount

def calculateSolidLayerCount():
	layerHeight = getProfileSettingFloat('layer_height')
	solidThickness = getProfileSettingFloat('solid_layer_thickness')
	if layerHeight == 0.0:
		return 1
	return int(math.ceil(solidThickness / (layerHeight - 0.0001)))

def calculateObjectSizeOffsets():
	size = 0.0

	if getProfileSetting('platform_adhesion') == 'Brim':
		size += getProfileSettingFloat('brim_line_count') * calculateEdgeWidth()
	elif getProfileSetting('platform_adhesion') == 'Raft':
		pass
	else:
		if getProfileSettingFloat('skirt_line_count') > 0:
			size += getProfileSettingFloat('skirt_line_count') * calculateEdgeWidth() + getProfileSettingFloat('skirt_gap')
	return [size, size]

def getMachineCenterCoords():
	if getMachineSetting('machine_center_is_zero') == 'True':
		return [0, 0]
	return [getMachineSettingFloat('machine_width') / 2, getMachineSettingFloat('machine_depth') / 2]

#Returns a list of convex polygons, first polygon is the allowed area of the machine,
# the rest of the polygons are the dis-allowed areas of the machine.
def getMachineSizePolygons():
	size = numpy.array([getMachineSettingFloat('machine_width'), getMachineSettingFloat('machine_depth'), getMachineSettingFloat('machine_height')], numpy.float32)
	ret = []
	if getMachineSetting('machine_shape') == 'Circular':
		# Circle platform for delta printers...
		circle = []
		steps = 32
		for n in range(0, steps):
			circle.append([math.cos(float(n)/steps*2*math.pi) * size[0]/2, math.sin(float(n)/steps*2*math.pi) * size[1]/2])
		ret.append(numpy.array(circle, numpy.float32))
	else:
		ret.append(numpy.array([[-size[0]/2,-size[1]/2],[size[0]/2,-size[1]/2],[size[0]/2, size[1]/2], [-size[0]/2, size[1]/2]], numpy.float32))

	if getMachineSetting('machine_type') == 'ultimaker2':
		#UM2 no-go zones
		w = 25
		h = 10
		ret.append(numpy.array([[-size[0]/2,-size[1]/2],[-size[0]/2+w+2,-size[1]/2], [-size[0]/2+w,-size[1]/2+h], [-size[0]/2,-size[1]/2+h]], numpy.float32))
		ret.append(numpy.array([[ size[0]/2-w-2,-size[1]/2],[ size[0]/2,-size[1]/2], [ size[0]/2,-size[1]/2+h],[ size[0]/2-w,-size[1]/2+h]], numpy.float32))
		ret.append(numpy.array([[-size[0]/2+w+2, size[1]/2],[-size[0]/2, size[1]/2], [-size[0]/2, size[1]/2-h],[-size[0]/2+w, size[1]/2-h]], numpy.float32))
		ret.append(numpy.array([[ size[0]/2, size[1]/2],[ size[0]/2-w-2, size[1]/2], [ size[0]/2-w, size[1]/2-h],[ size[0]/2, size[1]/2-h]], numpy.float32))
	return ret

#returns the number of extruders minimal used. Normally this returns 1, but with dual-extrusion support material it returns 2
def minimalExtruderCount():
	if int(getMachineSetting('extruder_amount')) < 2:
		return 1
	if getProfileSetting('support') == 'None':
		return 1
	if int(getProfileSetting('start_extruder')) == 0 and getProfileSetting('support_dual_extrusion') == 'Second extruder':
		return 2
	if int(getProfileSetting('start_extruder')) == 1 and getProfileSetting('support_dual_extrusion') == 'First extruder':
		return 2
	return 1

def getGCodeExtension():
	if getMachineSetting('gcode_flavor') == 'BFB':
		return '.bfb'
	return '.g'

#########################################################
## Alteration file functions
#########################################################

def getPalpeurGCode():
	if getProfileSetting('sensor') == 'Disabled':
		return ';No Sensor'
	if getProfileSetting('sensor') == 'Enabled':
		return 'G29'

def moveToWipeTowerCenter():
	layer_height = getProfileSettingFloat('layer_height')
	wipe_tower_volume = getProfileSettingFloat('wipe_tower_volume')
	wipe_tower_shape = getProfileSetting('wipe_tower_shape').lower()

	wipe_tower_half_size = 0
	if wipe_tower_shape in ["corner", "dumbbell", "crenel", "wall", "rectangle"]:
		wipe_tower_half_size = 0
	elif wipe_tower_shape == 'donut':
		wipe_tower_half_size = round(math.sqrt((4 * wipe_tower_volume) / (3 * math.pi * layer_height)) / 2, 3)
	else:
		wipe_tower_half_size = round(math.sqrt(wipe_tower_volume / layer_height) / 2, 3)

	wipe_tower_z_hop = getProfileSettingFloat('wipe_tower_z_hop')
	if wipe_tower_half_size == 0:
		if wipe_tower_z_hop == 0:
			return ";No move to wipe tower center"
		else:
			return "G91\nG0 F6000 Z-" + str(wipe_tower_z_hop) + "\nG90"
	else:
		if wipe_tower_z_hop == 0:
			return "G91\nG0 F6000 X-" + str(wipe_tower_half_size) + " Y" + str(wipe_tower_half_size) + "\nG90"
		else:
			return "G91\nG0 F6000 X-" + str(wipe_tower_half_size) + " Y" + str(wipe_tower_half_size) + " Z-" + str(wipe_tower_z_hop) + "\nG90"

def moveFromWipeTowerCenter():
	layer_height = getProfileSettingFloat('layer_height')
	wipe_tower_volume = getProfileSettingFloat('wipe_tower_volume')
	wipe_tower_shape = getProfileSetting('wipe_tower_shape').lower()

	wipe_tower_half_size = 0
	if wipe_tower_shape in ["corner", "dumbbell", "crenel", "wall", "rectangle"]:
		wipe_tower_half_size = 0
	elif wipe_tower_shape == 'donut':
		wipe_tower_half_size = round(math.sqrt((4 * wipe_tower_volume) / (3 * math.pi * layer_height)) / 2, 3)
	else:
		wipe_tower_half_size = round(math.sqrt(wipe_tower_volume / layer_height) / 2, 3)

	wipe_tower_z_hop = getProfileSettingFloat('wipe_tower_z_hop')
	if wipe_tower_half_size == 0:
		return ";No move from wipe tower center"
	else:
		return "G91\nG0 F6000 X" + str(wipe_tower_half_size) + " Y-" + str(wipe_tower_half_size) + "\nG90"

def replaceTagMatch(m):
	pre = m.group(1)
	tag = m.group(2)

	if tag == 'time':
		return pre + time.strftime('%H:%M:%S')
	
	if tag == 'machine_name':
		return pre + getMachineSetting('machine_name')

	if tag == 'app_version':
		return ' ' + os.environ['CURABYDAGO_VERSION']
	
	if tag == 'start_extruder':
		return pre + getProfileSetting('start_extruder')

	if tag == 'initial_retraction_amount':
		if int(getProfileSetting('start_extruder')) == 0:
			return pre + str(getProfileSettingFloat('retraction_amount'))
		else:
			return pre + str(getProfileSettingFloat('retraction_amount2'))

	if tag == 'initial_print_temperature':
		if int(getProfileSetting('start_extruder')) == 0:
			return pre + str(getProfileSettingFloat('print_temperature'))
		else:
			return pre + str(getProfileSettingFloat('print_temperature2'))

	if tag == 'addons':
		addons = []
		if getMachineSettingInt('extruder_amount') > 1:
			addons.append('Bicolor')
		if getMachineSettingFloat('machine_width') > 205:
			addons.append('XL')
		
		if len(addons) > 0:
			return ' ' + ', '.join(addons)
		else:
			return ' No addons'

	if tag == 'support_info':
		return ' ' + getProfileSetting('support')

	if tag == 'filament_info':
		return ' ' + getPreference('filament_name') + ' ' + getPreference('color_label')

	if tag == 'filament2_info':
		return ' ' + getPreference('filament2_name') + ' ' + getPreference('color2_label')

	if tag == 'print_temperature_info':
		return pre + str(getProfileSettingFloat('print_temperature')) + ' °C'

	if tag == 'print_temperature2_info':
		return pre + str(getProfileSettingFloat('print_temperature2')) + ' °C'

	if tag == 'sensor':
		return getPalpeurGCode()
	
	if tag == 'print_speed_info':
		return pre + str(getProfileSettingFloat('print_speed')) + ' mm/s'

	if tag == 'move_to_wipe_tower_center':
		return moveToWipeTowerCenter()

	if tag == 'move_from_wipe_tower_center':
		return moveFromWipeTowerCenter()

	if tag == 'set_target_temperature':
		print_temperature = getProfileSettingFloat('print_temperature')
		print_temperature2 = getProfileSettingFloat('print_temperature2')
		if print_temperature == print_temperature2:
			return ";No temperature change"
		else:
			return "M104 S" + str(print_temperature)

	if tag == 'set_target_temperature2':
		print_temperature = getProfileSettingFloat('print_temperature')
		print_temperature2 = getProfileSettingFloat('print_temperature2')
		if print_temperature == print_temperature2:
			return ";No temperature change"
		else:
			return "M104 S" + str(print_temperature2)

	if tag == 'check_filrunout':
		wipe_tower = int(getMachineSetting('extruder_amount')) > 1 and ((not getProfileSetting('support') == 'None' and getProfileSetting('support_dual_extrusion') == 'Second extruder') or mergeDone)
		if wipe_tower:
			if int(getProfileSetting('start_extruder')) == 0:
				return ";Filrunout 2 is enabled"
			else:
				return ";Filrunout 1 is enabled"
		else:
			if int(getProfileSetting('start_extruder')) == 0:
				return "D131 E1"
			else:
				return "D131 E0"

	if tag == 'retraction_amount':
		return pre + str(getProfileSettingFloat('retraction_amount'))
	
	if tag == 'retraction_amount_info':
		return pre + str(getProfileSettingFloat('retraction_amount')) + ' mm'
	
	if tag == 'retraction_speed_info':
		return pre + str(getProfileSettingFloat('retraction_speed')) + ' mm/s'
	
	if tag == 'flow_info':
		return pre + str(getProfileSettingFloat('filament_flow')) + ' %'

	if tag == 'start_retraction_amount':
		return pre + str(getProfileSettingFloat('start_retraction_amount'))

	if tag == 'switch_default_retraction_offset':
		return pre + str(getProfileSettingFloat('switch_default_retraction_offset'))

	if tag == 'switch_default_retraction_amount':
		return pre + str(getProfileSettingFloat('switch_default_retraction_amount'))

	if tag == 'pre_retraction_amount':
		return pre + str(getProfileSettingFloat('switch_default_retraction_amount') - getProfileSettingFloat('retraction_amount'))

	if tag == 'post_retraction_amount':
		return pre + str(getProfileSettingFloat('switch_default_retraction_amount') + getProfileSettingFloat('retraction_amount'))

	if tag == 'retraction_amount2':
		return pre + str(getProfileSettingFloat('retraction_amount2'))
	
	if tag == 'retraction_amount2_info':
		return pre + str(getProfileSettingFloat('retraction_amount2')) + ' mm'
	
	if tag == 'retraction_speed2_info':
		return pre + str(getProfileSettingFloat('retraction_speed2')) + ' mm/s'
	
	if tag == 'flow2_info':
		return pre + str(getProfileSettingFloat('filament_flow2')) + ' %'

	if tag == 'pre_retraction_amount2':
		return pre + str(getProfileSettingFloat('switch_default_retraction_amount') - getProfileSettingFloat('retraction_amount2'))

	if tag == 'post_retraction_amount2':
		return pre + str(getProfileSettingFloat('switch_default_retraction_amount') + getProfileSettingFloat('retraction_amount2'))

	if tag == 'z_offset':
		return pre + str(getProfileSettingFloat('offset_value'))
	
	if tag == 'layer_height_info':
		return pre + str(getProfileSettingFloat('layer_height')) + ' mm'
	
	if tag == 'fill_density_info':
		return pre + str(getProfileSettingFloat('fill_density')) + " %"

	if tag == 'date':
		return pre + time.strftime('%d-%m-%Y')
	if tag == 'day':
		return pre + ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][int(time.strftime('%w'))]
	if tag == 'print_time':
		return pre + '#P_TIME#'
	if tag == 'filament_amount':
		return pre + '#F_AMNT#'
	if tag == 'filament_weight':
		return pre + '#F_WGHT#'
	if tag == 'filament_cost':
		return pre + '#F_COST#'
	if tag == 'profile_string':
		return pre + 'CURA_PROFILE_STRING:%s' % (getProfileString())
	if pre == 'F' and tag == 'max_z_speed':
		f = getProfileSettingFloat('travel_speed') * 60
	if pre == 'F' and tag in ['print_speed', 'retraction_speed', 'travel_speed', 'bottom_layer_speed', 'cool_min_feedrate']:
		f = getProfileSettingFloat(tag) * 60
	elif isProfileSetting(tag):
		f = getProfileSettingFloat(tag)
	elif isPreference(tag):
		f = getProfileSettingFloat(tag)
	else:
		return '%s?%s?' % (pre, tag)
	if (f % 1) == 0:
		return pre + str(int(f))
	return pre + str(f)

def replaceGCodeTags(filename, gcodeInt):
	f = open(filename, 'r+')
	data = f.read(2048)
	data = data.replace('#P_TIME#', ('%5d:%02d' % (int(gcodeInt.totalMoveTimeMinute / 60), int(gcodeInt.totalMoveTimeMinute % 60)))[-8:])
	data = data.replace('#F_AMNT#', ('%8.2f' % (gcodeInt.extrusionAmount / 1000))[-8:])
	data = data.replace('#F_WGHT#', ('%8.2f' % (gcodeInt.calculateWeight() * 1000))[-8:])
	cost = gcodeInt.calculateCost()
	if cost is None:
		cost = 'Unknown'
	data = data.replace('#F_COST#', ('%8s' % (cost.split(' ')[0]))[-8:])
	f.seek(0)
	f.write(data)
	f.close()

def replaceGCodeTagsFromSlicer(filename, slicerInt):
	f = open(filename, 'r+')
	data = f.read(2048)
	data = data.replace('#P_TIME#', ('%8.2f' % (int(slicerInt._printTimeSeconds)))[-8:])
	data = data.replace('#F_AMNT#', ('%8.2f' % (slicerInt._filamentMM[0]))[-8:])
	data = data.replace('#F_WGHT#', ('%8.2f' % (float(slicerInt.getFilamentWeight()) * 1000))[-8:])
	cost = slicerInt.getFilamentCost()
	if cost is None:
		cost = 'Unknown'
	data = data.replace('#F_COST#', ('%8s' % (cost.split(' ')[0]))[-8:])
	f.seek(0)
	f.write(data)
	f.close()

### Get aleration raw contents. (Used internally in Cura)
def getAlterationFile(filename):
	if filename in tempOverride:
		return tempOverride[filename]
	global settingsDictionary
	if filename in settingsDictionary and settingsDictionary[filename].isAlteration():
		return settingsDictionary[filename].getValue()
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in alteration settings\n' % (filename))
	return ''

def setAlterationFile(name, value):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isAlteration():
		settingsDictionary[name].setValue(value)
	saveProfile(getDefaultProfilePath(), True)

def isTagIn(tag, contents):
	contents = re.sub(';[^\n]*\n', '', contents)
	return tag in contents

### Get the alteration file for output. (Used by Skeinforge)
def getAlterationFileContents(filename, extruderCount = 1):
	prefix = ''
	postfix = ''
	alterationContents = getAlterationFile(filename)
	return str(prefix + re.sub("(.)\{([^\}]*)\}", replaceTagMatch, alterationContents).rstrip() + '\n' + postfix).strip() + '\n'

def printSlicingInfo():
	print('********* Slicing parameters *********')
	print("print_temperature : ", getProfileSetting('print_temperature'))
	print("filament_diameter : ", getProfileSetting('filament_diameter'))
	print("filament_flow : ", getProfileSetting('filament_flow'))
	print("retraction_speed : ", getProfileSetting('retraction_speed'))
	print("retraction_amount : ", getProfileSetting('retraction_amount'))
	print("filament_physical_density : ", getProfileSetting('filament_physical_density'))
	print("filament_cost_kg : ", getProfileSetting('filament_cost_kg'))
	if int(getMachineSetting('extruder_amount')) == 2:
		print("print_temperature2 : ", getProfileSetting('print_temperature2'))
		print("filament_diameter2 : ", getProfileSetting('filament_diameter2'))
		print("filament_flow2 : ", getProfileSetting('filament_flow2'))
		print("retraction_speed2 : ", getProfileSetting('retraction_speed2'))
		print("retraction_amount2 : ", getProfileSetting('retraction_amount2'))
		print("filament_physical_density2 : ", getProfileSetting('filament_physical_density2'))
		print("filament_cost_kg2 : ", getProfileSetting('filament_cost_kg2'))
	print("extruder_amount : ", getMachineSetting('extruder_amount'))
	print("nozzle_size : ", getMachineSetting('nozzle_size'))
	print("rectration_enable : ", getMachineSetting('retraction_enable'))
	print("fan_full_height : ", getProfileSetting('fan_full_height'))
	print("fan_speed : ", getProfileSetting('fan_speed'))
	print("fan_speed_max : ", getProfileSetting('fan_speed_max'))
	print("coll_min_feedrate : ", getProfileSetting('cool_min_feedrate'))
	print("fill_density", getProfileSetting('fill_density'))
	print("layer_height ", getProfileSetting('layer_height'))
	print("solid_layer_thickness : ", getProfileSetting('solid_layer_thickness'))
	print("wall_thickness : ", getProfileSetting('wall_thickness'))
	print("print_speed : ", getProfileSetting('print_speed'))
	print("travel_speed : ", getProfileSetting('travel_speed'))
	print("bottom_layer_speed : ", getProfileSetting('bottom_layer_speed'))
	print("infill_speed : ", getProfileSetting('infill_speed'))
	print("solidarea_speed : ", getProfileSetting('solidarea_speed'))
	print("inset0_speed : ", getProfileSetting('inset0_speed'))
	print("insetx_speed : ", getProfileSetting('insetx_speed'))
	print("fan_speed ", getProfileSetting('fan_speed'))
	print("cool_min_layer_time : ", getProfileSetting('cool_min_layer_time'))
	print("support : ", getProfileSetting('support'))
	print("platform_adhesion : ", getProfileSetting('platform_adhesion'))
	print("sensor : ", getProfileSetting('sensor'))
	print('**************************************')
