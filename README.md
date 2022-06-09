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

### Introduction
The slicer binary is built on the fly. It is a full C++ project. The compilation process is based on standard Makefile.

## Using a virtual Python environment

Download and use a Python3.x universal installer from [Python website](https://www.python.org/downloads). In this project, we are using [Python3.9.12](https://www.python.org/ftp/python/3.9.12/python-3.9.12-macos11.pkg).

### Windows
In the project folder, open a terminate and, to create a virtual environment ("venv") with the python version you've just installed, execute :
```
python -m venv venv
```
If you have several python versions installed on your computer, instead of ```python```, please write the exact path to your python.exe file.

To activate your venv, type :
```
./venv/Scripts/activate
```

### Linux
- Install required packages
```
$ sudo apt install python3-venv libsdl2-2.0-0
```
- Set up and activate the virtual environment
```
$ python -m venv venv
$ ./venv/bin/activate
```

### Installing the python modules
If necesary, upgrade pip with :
```
pip install --upgrade pip
```
To install the necesary python modules, we will use python wheels :
```
pip install -r ./requirements.txt
```
If PyOpenGL and/or PyOpenGL_accelerate doesn't install correctly, please retry after download files you need from [Python website](https://pypi.org/project/PyOpenGL/#files) :
- PyOpenGL : PyOpenGL-3.1.6-cp39-cp39-win_amd64.whl
- PyOpenGL : PyOpenGL_accelerate-3.1.6-cp39-cp39-win_amd64.whl

On MacOS, please install these modules :
```
pip install pyobjc
pip install py2app
```

## Packaging
To create a package, execute from your project folder :
```
./package.sh <os> <architecture>
```
For example, on Windows, with a 64bits-architecture, write :
```
./package.sh windows 64 1
```
```1``` is a default parameter which means that you also want to build CuraEngine. Replace it by ```0``` if you've already built it once before.

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
