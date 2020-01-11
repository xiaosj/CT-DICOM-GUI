import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidgetItem, QMessageBox

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os
import pydicom
import numpy as np

from ct_image import ct_img

class myApp(QMainWindow):
    def __init__(self):
        super(myApp, self).__init__()
        uic.loadUi('CT_gui.ui', self)

        self.spinBoxList = [
            [spinBox_x0, spinBox_y0, spinBox_z0],
            [spinBox_x1, spinBox_y1, spinBox_z1],
            [spinBox_x2, spinBox_y2, spinBox_z2] ]
            
        # signal actions
        self.botton_open_folder.clicked.connect(self.openFolder)
        self.botton_open_file.clicked.connect(self.openFile)
        
        # add matplotlib canvas
        fig = plt.figure(figsize=(5.12, 5.12), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.axis('off')
        self.canvas = FigureCanvas(fig)
        self.canvas.setParent(self)

    def showErrMsg(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.setWindowTitle('Error')
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def openFolder(self):
        self.folder = QFileDialog.getExistingDirectory(self, 'Select Directory', '.')
        if self.folder:
            # sort file list by slice location (small to large)
            files = [f for f in os.listdir(self.folder) if f.endswith('.dcm')]
            if(len(files) > 0):
                self.ct = ct_img(self.folder)
            else:
                self.showErrMsg('No DICOM files (.dcm) are found in the selected folder.')

            # # write to list
            # self.listFiles.clear()
            # for i in range(len(files)):
            #     item = QListWidgetItem(files[i])
            #     if i % 2:
            #         item.setBackground(QColor('#d0d0d0'))
            #     self.listFiles.addItem(item)
        return

    def openFile(self):
        filename = QFileDialog.getOpenFileName(self, filter='.img')
        # if filename:

        return
    
    def display(self):
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
        # DICOM_display = '{:d} x {:d} pixels, {:.3f} x {:.3f} x {:.3f} mm\n'.format(nx, ny, dx, dy, dz)
        # DICOM_display += 'Patient Z Position: {:.2f}\n'.format(ds.ImagePositionPatient[2])
        # DICOM_display += 'Slice Location: {:.2f}\n'.format(ds.SliceLocation)
        # DICOM_display += 'Rescale Slope: {:}\n'.format(ds.RescaleSlope)
        # DICOM_display += 'Rescale Intercept: {:}\n'.format(ds.RescaleIntercept)
        # try:
        #     DICOM_display += 'Rescale RescaleType: {:}\n'.format(ds.RescaleType)
        # except:
        #     DICOM_display += 'Rescale RescaleType: Not Defined'
        # self.labelDICOM.setText(DICOM_display)
        
        return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = myApp()
    window.show()
    sys.exit(app.exec_())
