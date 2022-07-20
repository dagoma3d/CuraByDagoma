# How to add a new setting in Cura By Dagoma #
If you want to see complete examples, see pull requests #71 (radio-box), #80 (text-input with post-process), or #108 (check-box).
Under each step, there is a permalink to a line code. It shows the place to write the new line code.
If your setting is affected by bicolor printing, you can use this line to 

## Profile Setting (profile.py) ##
If your setting isn't implemented yet, your can create it or modify it : 
https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/util/profile.py#L183

## User Interface (mainWindow.py) ##
1) Create a function ```init...``` to declare your widget and set a default value https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/gui/mainWindow.py#L788
2) Call this function in ```loadConfiguration``` https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/gui/mainWindow.py#L592
3) 
