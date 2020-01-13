# CT-DICOM-GUI
This is a GUI tool based on Qt to display CT DICOM images and convert it to files for dose calculations.

![Image](https://github.com/xiaosj/CT-DICOM-GUI/raw/master/pictures/screen_cut.png)

## CT_gui.py(ui)
Main GUI file and the UI file from Qt Designer.

## ct_image.py
The class to handle DICOM files and data format conversion.  This class can also be used independently with the GUI.

## Dependence
* `pydicom`
* `PyQt5`


## img_resize.c
A C-program (for performance) to resample voxel based the volume-average.

Usage: `img_resize [img_file] [new_dx] [new_dy] [new_dz]`. The new voxel sizes are in the unit of mm.