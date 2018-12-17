# Cura by Dagoma
## About

Cura by Dagoma was originally forked from Legacy Cura.
It is built with the following components:
- [LegacyCura](https://github.com/daid/LegacyCura)
- [CuraEngine](https://github.com/Ultimaker/CuraEngine)
- [Clipper](http://www.angusj.com/delphi/clipper.php)
- [Python 2.7](http://python.org/)
- [wxPython](http://www.wxpython.org/)
- [PyOpenGL](http://pyopengl.sourceforge.net/)
- [PySerial](http://pyserial.sourceforge.net/)
- [NumPy](http://www.numpy.org/)

Windows only :
- [VideoCapture](http://videocapture.sourceforge.net/)
- [comtypes](http://starship.python.net/crew/theller/comtypes/)
- [EjectMedia](http://www.uwe-sieber.de/english.html)

## Packaging

### Introduction
The slicer binary is built on the fly. It is a full C++ project. The compilation process is based on standard Makefile.

### MacOS
For MacOS, it is necessary to use virtualenv and virtualwrapper to create a isolated python environment.
Moreover, wxPython 3.0.1 sources has a bug impacting MacOS and a patch must be applied before compiling it.
More details asap.

### Windows
Here are the needed requirement:
- A gcc compiler (from mingw64)
- Nsis 2.51 (as the nsis script uses the InstallOptions plugin, available on 2.xx versions).
- 7zip 9.20 as extraction is handled differently with newer versions.

TODO: Modify (nsis and packaging) scripts so that we can use the lastest tools versions.

The needed binaries (eg. PortablePython) are retrieved and used during the packaging process so it must work pretty flawlessly.


### Linux
For linux, two types of packages can be built:
- A debian package for Debian based distributions.
- A generic tar.gz archive for other distributions.

Nothing special is required for linux packaging, it should work natively.

## Engine useful discussions

### About spiralize mode

Bottom layer:
https://github.com/Ultimaker/CuraEngine/issues/51

Stutter:
https://github.com/Ultimaker/CuraEngine/issues/214
https://github.com/Ultimaker/CuraEngine/issues/424
