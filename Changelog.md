# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2018-12-08
- Separate the config files according to printer options.
- Remove some filaments in Neva/Magis configuration.
- Hide diameter option for Magis.
- Remove flex filament for dual extrusion option.
- Change the travel speed to 75mm/s (instead of 100mm/s) when printing in 0.2 mm.

## [2.1.0] - 2018-11-12
- Change the way printer options are handled.
- Introduce the dual-extrusion feature and all the stuff around.
- More information for the end user when he changes the application language.
- Add nozzle warmup progress bar to gcode start.
- Improves printers profiles and make them more flexible to use independently.
- Fix various bugs (gcode loading, linux + Wayland,...).
- Introduce specific profiles for different nozzle sizes.
- The ini folder is now dependent of the software version.
- Add the Disco Ultimate printer.
- Make printer addition easier.
- Add some filaments and enhance print parameters.

## [2.0.0] - 2018-03-01
- New unified packaging: It implies a brand new software icon used in the application and in installation info for the various OS.
- The configuration wizard allows to select the printer.
- For each printer, the parameters and their behaviors are the very same as the printer-specific version (it implies discovery users have finally an available update for their machine).
- No more preferences window but a Preferences menu item gathering the ability to change language and printer.
- Refine xml again.
- Set the model color to the color chosen by the user.
- The printerhead xml island (introduced in a previous version of Cura by Dagoma when the discoeasy200 printer head v3 was released) is no more needed when not necessary (ie. when a single version of the printer head is available).
- Spiralize mode now available.
- Remove xml islands on which the user has no way to modify parameters (linked to engine enumerations).

## [1.0.7] - 2017-12-01
- Fix crashes when changing a parameter during the slicing process.
- Add a filament color combo box depending on the chosen filament.
- Add a warning message if 'Other PLA' is chosen.
- Add an about window.
- Add links to the customer support and the filament buy page (both related to the chosen language).
- XML file reformatted, refined and translated in english. The software is still compatible with the old xml format.
- Refine displayed print time for Neva.
- Update and align core components versions used for packaging: wxPython 3.0.2 and CuraEngine legacy.
- Both prepare print buttons have now the same behavior.
- The gcodes start/end are now set during the software loading (no more when the user change a parameter...).
- The ability to save the build plate is restored.
- Rework the slicing information display.
- Complete rework on the UI. Not really visible but a less felxible wxpython widget is used as our UI is pretty simple so no need to use a complex one.
- Rework and simplify the configuration wizard.
- USB printing : The stop/pause buttons behaviors reflect the ones related to physical buttons of printers.
- Print button actions order have changed: SD card auto save, USB print, manual save.

## [1.0.6] - 2017-07-01
- Add the color change feature.
- Fix some display bugs.

## [1.0.5] - 2017-03-01
- Fix various bugs.

## [1.0.4] - 2017-01-01
- Chosen parameters are saved and reloaded when turning off/on the software.

## [1.0.3] - 2016-11-01
- Rework the xml file to be sharper when changing a parameter.

## [1.0.2] - 2016-06-20
- Add fyberlogy HD filament.
- Force all in one print.
- Fix issue related to sensor.
- Version number now visible.
- New board drivers.
