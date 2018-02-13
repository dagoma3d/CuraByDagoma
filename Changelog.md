# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [1.0.8] - 2017-03-01
- The configuration wizard allows to select the printer.
- No more preferences window but a Preferences menu item gathering the ability to change language and printer.
- Refine xml again.
- Set the model color to the color chosen by the user.
- The printhead xml island (introduced in a previous version of Cura by Dagoma when the discoeasy200 printhead v3 was released) is no more needed when not necessary (ie. when a single version of the printhead is available)

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
