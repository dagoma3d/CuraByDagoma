# Global check for Cura By Dagoma
This sheet sums up every important tests we need to make before upload a new release.
These tests must be validated on Windows, Linux and MacOs.

To be sure the new version is ready to be distributed, please check the following statements.

## Global
- The ```readme```, ```changelog``` and ```requirements``` files are updated.
- The version number of the new release is written instead of the former one.
- The new improvements work with every printer, particularly with the bicolors.
- The profiles of the filaments and the printers are updated.

## Package and installation
- Cura Engine is well downloaded and packaged.
- The package is created normally.
- The installation runs.
- The default path for installation matches with the OS.
- The drivers are correclty installed.
- A shortcut is created in the start menu and on the desktop.
- The shortcuts start the application.
- The application runs well.

## Slicing
- Print objects with and without supports, adding a skirt, a brim or a raft. Checking visually the layers in the software is quicker.
- The maximal printable area is correct, according to skirt, brim and raft.

## GUI
- There is nothing abnormal in graphics (lack of transparency, size of the widgets...).
- All the strings are translated in French and English.
- All the icons and images are updated.
- The ```About``` window is updated.
- Every action in the menu bar works well.
- The two links ```Buy filament``` and ```Fine tune your settings``` are updated.

## Saving G-Code
- G-Code can be saved on the computer.
- G-Start is updated.
- The computer can detect, save in, and eject SD-cards.

## Serial Communication
- The software can send G-Code to the printer.
- The warning window's message matches with battery level.

## Uninstalling
- The uninstaller can run.
- The folder and all the files related tu Cura By Dagoma are deleted.
- The shortcuts (in the start menu and on the desktop) disappear.
