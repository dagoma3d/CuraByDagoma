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

#### Install Python2.7 (non-system, framework-based)

- Download and install https://www.python.org/ftp/python/2.7.18/python-2.7.18-macosx10.9.pkg

#### Install and Use VirtualWrapper

Virtualwrapper is necessary to be able to get a standalone python, otherwise it will use the python available on the computer.

```
pip install virtualenvwrapper
export WORKON_HOME=~/Envs
mkdir -p $WORKON_HOME
source `which virtualenvwrapper.sh`
mkvirtualenv Cura
```

#### Virtualwrapper commands

```
deactivate #deactivate virtualenv
workon Cura #use Cura virtualenv
```

#### Compile CuraByDagoma

```
mkdir CuraByDagoma
cd CuraByDagoma
git clone https://github.com/wxWidgets/wxWidgets
cd wxWidgets
git checkout wxPy-3.0-branch

./configure \
 CPPFLAGS=-D__ASSERT_MACROS_DEFINE_VERSIONS_WITHOUT_UNDERSCORES=1 \
 CFLAGS='-msse2 -mno-sse3 -mno-sse4' \
 CXXFLAGS='-msse2 -mno-sse3 -mno-sse4' \
 --disable-debug \
 --disable-mediactrl \
 --enable-clipboard \
 --enable-display \
 --enable-dnd \
 --enable-monolithic \
 --enable-optimise \
 --enable-std_string \
 --enable-svg \
 --enable-macosx_arch=x86_64 \
 --enable-webkit \
 --prefix=$HOME/Envs/Cura/ \
 --with-expat \
 --with-libjpeg=builtin \
 --with-libpng=builtin \
 --with-libtiff=builtin \
 --with-macosx-version-min=10.9 \
 --with-opengl \
 --with-osx_cocoa \
 --with-zlib=builtin

make -j4 install

git clone https://github.com/wxWidgets/wxPython-Classic
cd wxPython-Classic
python setup.py build_ext \
 BUILD_GIZMOS=1 \
 BUILD_GLCANVAS=1 \
 BUILD_STC=1 \
 INSTALL_MULTIVERSION=0 \
 UNICODE=1 \
 WX_CONFIG=$HOME/Envs/Cura/bin/wx-config \
 WXPORT=osx_cocoa

python setup.py install \
 --prefix=/Users/waelabd/Envs/Cura \
 BUILD_GIZMOS=1 \
 BUILD_GLCANVAS=1 \
 BUILD_STC=1 \
 INSTALL_MULTIVERSION=0 \
 UNICODE=1 \
 WX_CONFIG=$HOME/Envs/Cura/bin/wx-config \
 WXPORT=osx_cocoa

cd ../../
git clone https://github.com/dagoma3d/CuraByDagoma
cd CuraByDagoma
pip install -r requirements_darwin.txt
./package.sh darwin 1
```

### MacOS (Old)
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
