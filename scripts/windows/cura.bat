@echo off

Set PYTHONHOME=%cd%\python3
Set PYTHONPATH=%cd%\python3\Lib

@python3\pythonw.exe -m Cura.cura %*
