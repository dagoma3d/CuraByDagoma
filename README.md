# Cura by Dagoma
## About

Cura by Dagoma was originally forked from Legacy Cura.
It is built with the following components:
- [LegacyCura](https://github.com/daid/LegacyCura)
- [CuraEngine](https://github.com/Ultimaker/CuraEngine)
- [Clipper](http://www.angusj.com/delphi/clipper.php)
- [Python 3.9](http://python.org/)
- [wxPython](http://www.wxpython.org/)
- [PyOpenGL](http://pyopengl.sourceforge.net/)
- [PySerial](http://pyserial.sourceforge.net/)
- [NumPy](http://www.numpy.org/)

Windows only :
- [EjectMedia](http://www.uwe-sieber.de/english.html)

## Packaging

### Introduction
The slicer binary is built on the fly. It is a full C++ project. The compilation process is based on standard Makefile.

### MacOS

#### Python 2.7

For MacOS, it is necessary to use virtualenv and virtualwrapper to create a isolated python environment.
Moreover, wxPython 3.0.1 sources has a bug impacting MacOS and a patch must be applied before compiling it.
Check out the following bug opened against wxWidgets : https://trac.wxwidgets.org/ticket/16329

According to this :
- The wxPython github project has been forked under dagoma3d workspace : https://github.com/dagoma3d/wxPython
- A new branch named 3.0.2 has been created from the wxPy-3.0.2.0 tag
- The patch has been applied on this branch.

Finally, to build the software on MacOS, please follow the instructions described on LegacyCura : https://github.com/daid/LegacyCura/#mac-os-x

To build it on El Capitan, the commands must be slightly modified:
```
./configure \
 CFLAGS='-msse2 -mno-sse3 -mno-sse4' \
 CXXFLAGS='-msse2 -mno-sse3 -mno-sse4' \
 --disable-debug \
 --enable-clipboard \
 --enable-display \
 --enable-dnd \
 --enable-monolithic \
 --enable-optimise \
 --enable-std_string \
 --enable-svg \
 --enable-macosx_arch=x86_64 \
 --enable-webkit \
 --prefix=$HOME/.virtualenvs/Cura/ \
 --with-expat \
 --with-libjpeg=builtin \
 --with-libpng=builtin \
 --with-libtiff=builtin \
 --with-macosx-version-min=10.9 \
 --with-opengl \
 --with-osx_cocoa \
 --with-zlib=builtin

python setup.py clean --all

python setup.py build_ext \
 BUILD_GIZMOS=1 \
 BUILD_GLCANVAS=1 \
 BUILD_STC=1 \
 INSTALL_MULTIVERSION=0 \
 UNICODE=1 \
 WX_CONFIG=$HOME/.virtualenvs/Cura/bin/wx-config \
 WXPORT=osx_cocoa

python setup.py install \
 --force \
 --prefix=$HOME/.virtualenvs/Cura \
 BUILD_GIZMOS=1 \
 BUILD_GLCANVAS=1 \
 BUILD_STC=1 \
 INSTALL_MULTIVERSION=0 \
 UNICODE=1 \
 WX_CONFIG=$HOME/.virtualenvs/Cura/bin/wx-config \
 WXPORT=osx_cocoa
```

#### Python 3.x

Download and use a Python3.x universal installer from [Python website](https://www.python.org/downloads/macos/). Let's say [Python3.9.12](https://www.python.org/ftp/python/3.9.12/python-3.9.12-macos11.pkg).

Create a virtual environement and activate it:
```
python -m venv Cura
. ./Cura/bin/activate
```

Install all dependencies except wxPython:
```
pip install wheel
pip install -r requirements.txt
pip install pyobjc
pip install py2app
```

Download the latest wxPython wheel matching your python version from [wxPython website](https://pypi.org/project/wxPython/#files). For Python 3.9, it is [wxPython-4.1.1-cp39-cp39-macosx_10_10_x86_64.whl](https://files.pythonhosted.org/packages/2c/a8/7027e8ca3ba20dc2ed2acd556e31941cb44097ab87d6f81d646a79de4eab/wxPython-4.1.1-cp39-cp39-macosx_10_10_x86_64.whl)

Install this wheel:
```
pip install wxPython-4.1.1-cp39-cp39-macosx_10_10_x86_64.whl
```

Apply [this commit](https://github.com/dagoma3d/PyOpenGL/commit/87e6b6e96e324ef3c89027c3c098da4b553569e5) to PyOpenGL.

You are ready to build.

### Windows
Here are the needed requirement:
- A gcc compiler (from mingw64)
- Nsis 3.08
- 7zip 9.20 as extraction is handled differently with newer versions.

The needed binaries (eg. PortablePython) are retrieved and used during the packaging process so it must work pretty flawlessly.


### Linux
For linux, two types of packages can be built:
- A debian package for Debian based distributions.
- A generic tar.gz archive for other distributions.

Nothing special is required for linux packaging, it should work natively.

### Migration from python2 to python3
The _migration_python3_ branch is still in development.

For now, the only available distribution package is the debian one:
https://drive.google.com/file/d/1M4feXfi3IyKtdsA5HAFySgIrI7Vo4CHA/view?usp=sharing

To install it :
```
$ sudo dpkg -i ./CuraByDagoma_amd64.deb
$ sudo apt install -f
```
or
```
$ sudo apt install ./CuraByDagoma_amd64.deb
```

#### Virtual environment
Using python virtual environment seems to work fine, to be investigated in order to provide an AppImage.

Instruction to set up the right environment :

- Install required packages

```
$ sudo apt install python3-venv libsdl2-2.0-0

```

- Set up and activate the virtual environment

```
$ python3 -m venv venv
$ ./venv/Scripts/activate
```

- Install dependencies

For wxPython, pre-compiled packages are available at https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
Depending on your OS and your python version, change the requirements.txt file accordingly.

Example : for ubuntu 18.04 and python 3.6 the right whl file to install is https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04/wxPython-4.1.0-cp36-cp36m-linux_x86_64.whl

**The default package listed in the requirements is related to ubuntu 20.04 and python 3.8.**

```
(venv)$ pip install -r requirements.txt
```

- Get CuraEngine binary file and make it executable
```
(venv)$ wget github.com/dagoma3d/CuraEngine/releases/latest/download/CuraEngine-linux_x86_64 -O CuraEngine
(venv)$ chmod +x CuraEngine
```

- All is ready, you just have to launch the app entry point
```
(venv)$ python cura.py
```

## Engine useful discussions

### About spiralize mode

Bottom layer:
https://github.com/Ultimaker/CuraEngine/issues/51

Stutter:
https://github.com/Ultimaker/CuraEngine/issues/214
https://github.com/Ultimaker/CuraEngine/issues/424
