# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [2.2.5] - 2024-02-04
- Review gettext usage
- Get latest release tag from GitHub (not dist anymore)

## [2.2.4] - 2024-01-30
- Introduces Sigma Pro 500z
- Add the ability to automatically change color at user defined layers (#137)

## [2.2.3] - 2023-03-10
- Stop searching temperature command in gcode end sequence
- Apply locale workaround when system locale is not equal to region locale

## [2.2.2] - 2022-11-24
Fix temperature order added to the end of the generated gcode when a single object is sliced from a dual extrusion printer

## [2.2.1] - 2022-11-02
- Fix save build plate feature
- Disable USB printing as it doesn't work as expected for now due to python migration
- Special characters in filenames are now correctly handled
- Rename PolyFlex label
- Fix minor graphical bugs
- Custom first layer temperature
- Add raft and skirt choices
- Add shorcut list in help menu
- Add bug report process in help menu
- Replace default example stl
- Fix desktop shortcut
- Fix Windows desktop shortcut launch path
- Change the first layer thickness according to build plate type (for delta printers only)
- Remove drivers installation from the windows installer. If needed, should be installed separately (https://github.com/dagoma3d/CuraByDagoma/tree/master/scripts/windows/drivers)

## [2.2.0] - 2022-06-27
- Migrate from Python 2.7 to Python 3.9
- Migrate from NSIS 2 to NSIS 3
- Update Dagoma icon and splash screen

## [2.1.9] - 2022-05-02
- Introduce new Sigma 0.8mm toolhead.

## [2.1.8] - 2022-03-29
- Introduce new Sigma printer.

## [2.1.7] - 2020-11-05
- Introduce Marble Chromatik filament.

## [2.1.6] - 2020-09-16
- Enhance Filo3D filament print parameters.

## [2.1.5] - 2019-11-29
- Allow user to select the initial extruder when a dual-extruder printer is used.
- Review the wipe tower size calculus.
- Stop wipe tower generation when a bicolor object ends with a single color.
- Transform n wipe tower infill lines into pure moves (no extrusion) to decrease the noozle pressure before going back to the object (n depends on the wipe tower thickness).
- Update all links targetting the website.
- Fix some minor bugs.

## [2.1.4] - 2019-09-11
- Fix wipe tower size issue.
- Align filament insertion/retraction at the beginning/end of the print.
- Fix a display bug related to the "new version available" feature.
- Fix a bug related to the print temperature of filament2 when changing quality.
- Remove the pause before moving to the wipe tower.
- Change print parameters for black and white Chromatik.
- Introduce new filaments.
- Introduce Disco XL addon.
- Disable grip temperature feature for Neva/Magis.
- Add opened stls names to the application's title.
- Update the lastfile param when opening file with drag and drop or file association.
- Enhance print information in gcode.

## [2.1.2] - 2019-02-18
- Remove filaments duplicates.
- Remove old filaments and add some missing ones.
- Change retraction speed for chromatik filaments.
- Change default support fill rate.
- Change default support z distance.
- Add some new filaments.
- Reactivate the "print one at a time" mode.
- Display again the consumed filament length.
- Enhance slice information display.
- Fix many minor bugs.
- Correctly handle some special use cases to make the usage more flexible regarding the print and printer types (combination of mono/bi color).
- Decrease the travel speed to minimize collision between the printed object and the nozzle.
- Decrease the travel speed for Neva/Magis.

## [2.1.1] - 2019-01-07
- Separate the config files according to printer options.
- Remove some filaments in Neva/Magis configuration.
- Hide diameter option for Magis.
- Remove flex filament for dual extrusion option.
- Change the travel speed to 75mm/s (instead of 100mm/s) when printing in 0.2 mm.
- Add Mate PLA.
- Introduce the minimum segment length parameter (exposed from CuraEngine).
- When deleting all objects in layer mode, reset view mode to normal.
- Make website links generic (finally one single url now...)
- Add a quick and dirty way to warn users when a new version is available.
- Rework around the wipe tower handling.

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
