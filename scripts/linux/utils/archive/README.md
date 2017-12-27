# Cura-by-dagoma-<MACHINE_NAME>
Cura-by-dagoma-<MACHINE_NAME> is a fork of Legacy Cura made by Dagoma for the Dagoma <MACHINE_NAME> printer.

# Specifications
Package: curabydago-<MACHINE_NAME_LOWERCASE>
Source: Dagoma
Version: <BUILD_VERSION>
Architecture: <BUILD_ARCHITECTURE>
Maintainer: Orel <orel@dagoma.fr>
Provides: curabydago-<MACHINE_NAME_LOWERCASE>
Dependencies:
* python2.7
* python-wxgtk2.8 | python-wxgtk3.0 | wxpython
* python-opengl | pyopengl
* python-serial | pyserial
* python-numpy | numpy

# How to:
After extracting the archive, and installing the required dependencies, just run the following command:
```
python2.7 ./curabydago-<MACHINE_NAME_LOWERCASE>/cura.py
```
Feel free to create your own launch script, desktop file,...

Have fun !
