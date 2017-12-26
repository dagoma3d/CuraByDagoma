# Cura-by-dagoma-#machine_name#
Cura-by-dagoma-#machine_name# is a fork of Legacy Cura made by Dagoma for the Dagoma #machine_name# printer.

# Specifications
Package: curabydago-#machine_name_lowercase#
Source: Dagoma
Version: #build_version#
Architecture: #build_architecture#
Maintainer: Orel <orel@dagoma.fr>
Provides: curabydago-#machine_name_lowercase#
Dependencies:
* python2.7
* python-wxgtk2.8 | python-wxgtk3.0 | wxpython
* python-opengl | pyopengl
* python-serial | pyserial
* python-numpy | numpy

# How to:
After extracting the archive, and installing the required dependencies, just run the following command:
```
python2.7 ./curabydago-#machine_name_lowercase#/cura.py
```
Feel free to create your own launch script, desktop file,...

Have fun !
