# How to add a new setting in Cura By Dagoma #
If you want to see complete examples, see pull requests #71 (radio-box), #80 (text-input, bicolor, post-process), or #108 (check-box).
Under each step, there is a permalink to a line code. It shows the place to write the new line code.
If your setting is affected by bicolor printing, you can use this line to 

## Profile Setting (profile.py) ##
If your setting isn't implemented yet, your can create it or modify it : 
https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/util/profile.py#L183

## User Interface (mainWindow.py) ##
1) Create a function ```init...``` to declare your widget and set a default value https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/gui/mainWindow.py#L788
2) Call this function in ```loadConfiguration``` https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/gui/mainWindow.py#L592
3) Add your widget to the window (the place of the line is important) https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L551
4) Create the refresh function. There are several ```putProfileSetting``` functions depending on the type of the setting (bool, float, ...) https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L1489
5) Create the function called by the widget (not binded for the moment). Don't forget ```self.updateSceneAndControls(event)``` at the end https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L1566
6) Then bind this function with the widget. The name of the event depends on the type of widget https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L480

The following steps depends on what you want to do with your setting, and what is already implemented.

## Applying the setting ##
