# Cura by Dagoma

Before releasing a new version, please read the [CHECK file](https://github.com/dagoma3d/CuraByDagoma/blob/03d59610ab4fe7f50b081df5210855dce89d94b6/CHECK.md).

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

## Using WinPython for Windows

WinPython is used for production. In development, we use a python virtual environment (see below).

First download WinPython according to your architecture system. In this project, we are using Python 3.9.10.
- Windows 64-bits : https://sourceforge.net/projects/winpython/files/WinPython_3.9/3.9.10.0/Winpython64-3.9.10.0dot.exe/download
- Windows 32-bits : https://sourceforge.net/projects/winpython/files/WinPython_3.9/3.9.10.0/Winpython32-3.9.10.0dot.exe/download

After extracting it, open the ```WinPython Command Prompt.exe``` in the WinPython folder. Download the necessary dependencies using pip :
```
pip install wheel setuptools pyserial wxPython
```
Then download the two following wheels from this [website](https://www.lfd.uci.edu/~gohlke/pythonlibs/#_pyopengl), according to your OS :
- Windows 64-bits : ```PyOpenGL-3.1.6-cp39-cp39-win_amd64.whl``` and ```PyOpenGL_accelerate-3.1.6-cp39-cp39-win_amd64.whl```
- Windows 32-bits : ```PyOpenGL‑3.1.6‑cp39‑cp39‑win32.whl``` and ```PyOpenGL_accelerate‑3.1.6‑cp310‑cp310‑win32.whl```

Finally copy the ```python-3.9.10.amd64``` folder (```python-3.9.10``` for Windows 32-bits) and paste it in your project root. After packaging, this folder will be renamed to ```python```.

## Using a virtual Python environment

Virtual Python environments have been used only during development. In production, for Windows, we use WinPython (see section above).

Download and use a Python3.x universal installer from [Python website](https://www.python.org/downloads). In this project, we are using [Python3.9.10](https://www.python.org/ftp/python/3.9.10/python-3.9.10-macos11.pkg).

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
Notice that you must activate your venv before every modification of the venv.

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
To install the necesary python modules, we will use python wheels.
Please use the requirements file linked to your OS, among the following list : 
- ```requirements_win_amd64.txt``` for Windows 64-bits
- ```requirements_win32.txt``` for Windows 32-bits
- ```requirements_ubuntu.txt``` for Ubuntu
- ```requirements_macos.txt``` for MacOs

For example, if you are on Windows 64-bits, type :
```
pip install -r ./requirements_win_amd64.txt
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

- Get CuraEngine binary file and make it executable
```
(venv)$ wget github.com/dagoma3d/CuraEngine/releases/latest/download/CuraEngine-linux_x86_64 -O CuraEngine
(venv)$ chmod +x CuraEngine
```

- All is ready, you just have to launch the app entry point
```
(venv)$ python cura.py
```

### About spiralize mode

Bottom layer:
https://github.com/Ultimaker/CuraEngine/issues/51

Stutter:
https://github.com/Ultimaker/CuraEngine/issues/214
https://github.com/Ultimaker/CuraEngine/issues/424
