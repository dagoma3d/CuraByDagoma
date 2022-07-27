# How to add a new setting in Cura By Dagoma #
If you want to see complete examples, see pull requests #71 (radio-box), #80 (text-input, bicolor, post-process), or #108 (check-box).
Under each step, there is a permalink to a line code. It shows the place to write the new line code.

If your setting is affected by bicolor printing, you can use this line to execute specific actions for bicolor printers : ```if int(profile.getMachineSetting('extruder_amount')) == 2```.

If necesary, don't forget to delete the files ```current_profile.ini```, ```mru_filelist.ini``` and ```preferences.ini``` to reset the settings of the app.

## Profile Setting (profile.py) ##
If your profile setting isn't implemented yet, your can create it or modify it : https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/util/profile.py#L191
If your setting value only depends on the printer, you can add it to the XML files. If your profile setting has the same name, it will be automatically updated. https://github.com/dagoma3d/CuraByDagoma/blob/0df98ce91c8eaf90b1a58e76bb4df625328a8206/resources/xml/sigma.xml#L537

## User Interface (mainWindow.py) ##
1) Create a function ```init...``` to declare your widget and set a default value https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/gui/mainWindow.py#L788
2) Call this function in ```loadConfiguration``` https://github.com/dagoma3d/CuraByDagoma/blob/73e31b1edd6957cfcdd55cfaed104c2c188952d9/Cura/gui/mainWindow.py#L592
3) Add your widget to the window (the place of the line is important) https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L551
4) Create the refresh function. There are several ```putProfileSetting``` functions depending on the type of the setting (bool, float, ...) https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L1489
5) Create the function called by the widget (not binded for the moment). Don't forget ```self.updateSceneAndControls(event)``` at the end https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L1566
6) Then bind this function with the widget. The name of the event depends on the type of widget https://github.com/dagoma3d/CuraByDagoma/blob/69a6f6374ebe84a4e66aec7989d70b82e1c53b5b/Cura/gui/mainWindow.py#L480

The following steps depends on what you want to do with your setting, and what is already implemented.
The next sections shows different possibilities.

## Applying the setting (profile.py) ##
If necesary, you can modify the ```settings``` dictionary depending on the value of your profile setting https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/util/sliceEngine.py#L626

## G-Start (XML) ##
If you must use your new setting in the G-start (or the G-end), you can simply write it between curly braces ```{...}```. It will be automatically replaced in the final G-code https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/resources/xml/sigma.xml#L640
If you want to write something more complex based on your new setting, like a complete sentence or the result of a calculation, you can write something between hash signs ```#...#``` and replace it in post-process (see section below) https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/resources/xml/sigma.xml#L604

## Post-process (sceneView.py) ##
To have a clearer code, you can capture the profileSetting in a variable before using it https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/gui/sceneView.py#L386
If you must replace something in the G-start, use the ```replace``` function on ```block0``` https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/gui/sceneView.py#L403
If you must modifiy or add something directly in the G-code, you can use the ```find``` function and write or rewrite a line with your new setting
https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/gui/sceneView.py#L420
https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/gui/sceneView.py#L422

## Debug log (profile.py) ##
If necesary, you can add a message to help debugging in ```printSlicingInfo``` https://github.com/dagoma3d/CuraByDagoma/blob/2c47737f64207b099294e5cfb3180767d56ed8e4/Cura/util/profile.py#L1346
