import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidgetItem

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os
import pydicom
import numpy as np

class myApp(QMainWindow):
    def __init__(self):
        super(myApp, self).__init__()
        uic.loadUi('CT_gui.ui', self)
        self.botton_open_folder.clicked.connect(self.openFolder)
        self.botton_open_file.clicked.connect(self.openFile)
        
        # add matplotlib canvas
        fig = plt.figure(figsize=(5.12, 5.12), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.axis('off')
        self.canvas = FigureCanvas(fig)
        self.canvas.setParent(self)

    def openFolder(self):
        self.folder = str(QFileDialog.getExistingDirectory(self, 'Select Directory', '.'))
        
        # sort file list by slice location (small to large)
        files = [f for f in os.listdir(self.folder) if f.endswith('.dcm')]
        file_z = []
        for f in files:
            ds = pydicom.dcmread(self.folder + '/' + f)
            z = float(ds.SliceLocation)
            file_z.append((f, z))
        # print(sorted(file_z, key=lambda tuple: tuple[1]))
        files = [f[0] for f in sorted(file_z, key=lambda tuple: tuple[1])]

        # write to list
        self.listFiles.clear()
        for i in range(len(files)):
            item = QListWidgetItem(files[i])
            if i % 2:
                item.setBackground(QColor('#d0d0d0'))
            self.listFiles.addItem(item)

    def openFile(self):
        filename = QFileDialog.getOpenFileName(self, filter='.img')
        return
    
    def selectFile(self, item):
        filename = item.text()
        self.check_CT(self.folder + '/' + filename)
        return

    def check_CT(self, filename):
        ds = pydicom.dcmread(filename)
        ct_data = ds.pixel_array
        npoint = 20
        icut = 8

        self.ax.clear()
        self.ax.imshow(ct_data, cmap='gray')
        (ny, nx) = ct_data.shape
        for _ in range(npoint):
            x = np.random.randint(nx//icut, nx//icut*(icut-1))
            y = np.random.randint(ny//icut, ny//icut*(icut-1))
            HU = ct_data[y, x]
            self.ax.text(x,y,'{:d}'.format(HU))
            self.ax.add_patch(Circle((x,y), nx/200, color='r'))
        self.ax.set_xlim((0, nx-1))
        self.ax.set_ylim((ny-1, 0))
        self.ax.axis('off')
        plt.tight_layout()
        self.canvas.draw()

        dx, dy = np.array(ds.PixelSpacing, dtype=np.float32)
        dz = np.float32(ds.SliceThickness)
        nx = ds.Columns
        ny = ds.Rows
        DICOM_display = '{:d} x {:d} pixels, {:.3f} x {:.3f} x {:.3f} mm\n'.format(nx, ny, dx, dy, dz)
        DICOM_display += 'Patient Z Position: {:.2f}\n'.format(ds.ImagePositionPatient[2])
        DICOM_display += 'Slice Location: {:.2f}\n'.format(ds.SliceLocation)
        DICOM_display += 'Rescale Slope: {:}\n'.format(ds.RescaleSlope)
        DICOM_display += 'Rescale Intercept: {:}\n'.format(ds.RescaleIntercept)
        try:
            DICOM_display += 'Rescale RescaleType: {:}\n'.format(ds.RescaleType)
        except:
            DICOM_display += 'Rescale RescaleType: Not Defined'
        self.labelDICOM.setText(DICOM_display)
        
        return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = myApp()
    window.show()
    sys.exit(app.exec_())
