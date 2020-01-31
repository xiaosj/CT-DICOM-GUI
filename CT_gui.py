import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem

import os
import struct
import pydicom
import numpy as np
from ct_image import ct_img

from matplotlib.backends.qt_compat import is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import FigureCanvas
else:
    from matplotlib.backends.backend_qt4agg import FigureCanvas

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import LogNorm

class myApp(QMainWindow):
    def __init__(self):
        super(myApp, self).__init__()
        uic.loadUi('CT_gui.ui', self)

        self.defaultWindowTitle = 'DICOM-CT Tool'
        self.setWindowTitle(self.defaultWindowTitle)
        
        self.table_DICOM.setColumnCount(2)
        self.table_DICOM.verticalHeader().setVisible(False)
        self.table_DICOM.horizontalHeader().setVisible(False)

        self.spinBoxList = [
            [self.spinBox_x0, self.spinBox_y0, self.spinBox_z0],
            [self.spinBox_x1, self.spinBox_y1, self.spinBox_z1],
            [self.spinBox_x2, self.spinBox_y2, self.spinBox_z2] ]
        self.with_dose = False
        self.hold_display_refresh = False
            
        # add matplotlib canvas
        self.fig = plt.figure(figsize=(8,6), dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.move(10,150)
        self.canvas.setParent(self)
        self.firstDraw = True
        self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        # self.addToolBar(NavigationToolbar(self.canvas, self))

        # signal actions
        self.botton_open_folder.clicked.connect(self.openFolder)
        self.botton_open_file.clicked.connect(self.openFile)
        self.botton_write_img.clicked.connect(self.saveImg)
        self.botton_open_dose.clicked.connect(self.openDose)
        self.checkBox_center_lines.stateChanged.connect(lambda:self.display(True))

        self.spinBox_x0.valueChanged.connect(self.spin0_value_changed)
        self.spinBox_y0.valueChanged.connect(self.spin0_value_changed)
        self.spinBox_z0.valueChanged.connect(self.spin0_value_changed)

        self.hSlider_x0.valueChanged.connect(self.slider_value_changed)
        self.hSlider_y0.valueChanged.connect(self.slider_value_changed)
        self.hSlider_z0.valueChanged.connect(self.slider_value_changed)

        for i in range(1,3):
            for spinBox in self.spinBoxList[i]:
                spinBox.valueChanged.connect(self.cut_value_changed)
        

    def showMsg(self, text, error=True):
        msg = QMessageBox()
        if error:
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Error')
        else:
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle('Information')
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()


    def openFolder(self):
        self.folder = QFileDialog.getExistingDirectory(self, 'Select Directory', '.')
        if self.folder:
            files = [f for f in os.listdir(self.folder) if f.endswith('.dcm')]
            if(len(files) > 0):
                self.ct = ct_img(self.folder)
                self.hold_display_refresh = True

                self.dicom_name = self.folder
                self.setWindowTitle(self.defaultWindowTitle + ': ' + self.dicom_name)

                self.table_DICOM.setRowCount(5)
                self.table_DICOM.setItem(0, 0, QTableWidgetItem('Voxel Num'))
                self.table_DICOM.setItem(0, 1, QTableWidgetItem('{:d} x {:d} x {:d}'.format(self.ct.nx, self.ct.ny, self.ct.nz)))
                self.table_DICOM.setItem(1, 0, QTableWidgetItem('Voxel Size'))
                self.table_DICOM.setItem(1, 1, QTableWidgetItem('{:.2f} x {:.2f} x {:.2f} mm'.format(self.ct.dx, self.ct.dy, self.ct.dz)))
            
                ds = pydicom.dcmread(files[0])
                self.table_DICOM.setItem(2, 0, QTableWidgetItem('Rescale Slope'))
                self.table_DICOM.setItem(2, 1, QTableWidgetItem('{:}'.format(ds.RescaleSlope)))
                self.table_DICOM.setItem(3, 0, QTableWidgetItem('Rescale Intercept'))
                self.table_DICOM.setItem(3, 1, QTableWidgetItem('{:}'.format(ds.RescaleIntercept)))
                try:
                    rescale_type = '{:}'.format(ds.RescaleType)
                except:
                    rescale_type = 'Not Defined'
                self.table_DICOM.setItem(4, 0, QTableWidgetItem('Rescale Type'))
                self.table_DICOM.setItem(4, 1, QTableWidgetItem(rescale_type))

                self.table_DICOM.resizeColumnsToContents()
                self.table_DICOM.resizeRowsToContents()

                self.setDefaultPlanes()
                self.botton_open_dose.setEnabled(True)

                self.display(True)
            else:
                self.showErrMsg('No DICOM files (.dcm) are found in the selected folder.')


    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Select Img File', filter='*.img')
        if filename:
            self.folder = os.path.dirname(filename)
            self.ct = ct_img(filename)
            self.hold_display_refresh = True

            self.dicom_name = os.path.basename(filename)
            self.setWindowTitle(self.defaultWindowTitle + ': ' + self.dicom_name)
            self.lineEdit_imgFilename.setText(os.path.basename(filename))
            self.botton_write_img.setEnabled(True)
            self.botton_open_dose.setEnabled(True)
            self.setDefaultPlanes()

            self.table_DICOM.setRowCount(2)
            self.table_DICOM.setItem(0, 0, QTableWidgetItem('Voxel Num'))
            self.table_DICOM.setItem(0, 1, QTableWidgetItem('{:d} x {:d} x {:d}'.format(self.ct.nx, self.ct.ny, self.ct.nz)))
            self.table_DICOM.setItem(1, 0, QTableWidgetItem('Voxel Size'))
            self.table_DICOM.setItem(1, 1, QTableWidgetItem('{:.2f} x {:.2f} x {:.2f} mm'.format(self.ct.dx, self.ct.dy, self.ct.dz)))
            self.table_DICOM.resizeColumnsToContents()
            self.table_DICOM.resizeRowsToContents()

            self.display(True)


    def openDose(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Select Dose File', filter='*.dose;*.err')
        if filename:
            try:
                self.ct.read_dose(filename)
                self.setWindowTitle(self.defaultWindowTitle + ': ' + self.dicom_name + ' + ' + os.path.basename(filename))
                self.hold_display_refresh = True
                self.spinBox_x0.setValue(self.ct.dose_x)
                self.spinBox_z0.setValue(self.ct.dose_z)
                self.with_dose = True
                self.display(True)
            except Exception as e:
                self.showMsg(str(e))


    def saveImg(self):
        filename = os.path.join(self.folder, self.lineEdit_imgFilename.text())
        if os.path.exists(filename):
            self.showMsg(filename + ' already exists')
        else:
            x1 = self.spinBox_x1.value()
            x2 = self.spinBox_x2.value()
            y1 = self.spinBox_y1.value()
            y2 = self.spinBox_y2.value()
            z1 = self.spinBox_z1.value()
            z2 = self.spinBox_z2.value()
            if not filename.endswith('.img'):
                filename += '.img'

            with open(filename, 'wb') as f:
                f.write(struct.pack('iii', x2-x1+1, y2-y1+1, z2-z1+1))
                f.write(struct.pack('fff', self.ct.dx, self.ct.dy, self.ct.dz))
                f.write(self.ct.voxel[z1:z2+1, y1:y2+1, x1:x2+1].tobytes())
                f.close()
                self.showMsg(filename + ' saved.', error=False)


    def setDefaultPlanes(self):
        # The maximum of spinBox and Slider must be set before setting their values
        for i in range(3):
            self.spinBoxList[i][0].setMaximum(self.ct.nx - 1)
            self.spinBoxList[i][1].setMaximum(self.ct.ny - 1)
            self.spinBoxList[i][2].setMaximum(self.ct.nz - 1)
        
        self.hSlider_x0.setMaximum(self.ct.nx - 1)
        self.hSlider_y0.setMaximum(self.ct.ny - 1)
        self.hSlider_z0.setMaximum(self.ct.nz - 1)

        self.spinBox_x0.setValue(self.ct.nx // 2)
        self.spinBox_y0.setValue(self.ct.ny // 2)
        self.spinBox_z0.setValue(self.ct.nz // 2)

        self.spinBox_x1.setValue(0)
        self.spinBox_y1.setValue(0)
        self.spinBox_z1.setValue(0)

        self.spinBox_x2.setValue(self.ct.nx - 1)
        self.spinBox_y2.setValue(self.ct.ny - 1)
        self.spinBox_z2.setValue(self.ct.nz - 1)


    def spin0_value_changed(self):
        sender = self.sender()
        if sender == self.spinBox_x0:
            self.hSlider_x0.setValue(self.spinBox_x0.value())
        if sender == self.spinBox_y0:
            self.hSlider_y0.setValue(self.spinBox_y0.value())
        if sender == self.spinBox_z0:
            self.hSlider_z0.setValue(self.spinBox_z0.value())
        self.display()


    def slider_value_changed(self):
        sender = self.sender()
        if sender == self.hSlider_x0:
            self.spinBox_x0.setValue(self.hSlider_x0.value())
        if sender == self.hSlider_y0:
            self.spinBox_y0.setValue(self.hSlider_y0.value())
        if sender == self.hSlider_z0:
            self.spinBox_z0.setValue(self.hSlider_z0.value())


    def cut_value_changed(self):
        self.spinBox_x1.setMaximum(self.spinBox_x2.value())
        self.spinBox_y1.setMaximum(self.spinBox_y2.value())
        self.spinBox_z1.setMaximum(self.spinBox_z2.value())

        self.spinBox_x2.setMinimum(self.spinBox_x1.value())
        self.spinBox_y2.setMinimum(self.spinBox_y1.value())
        self.spinBox_z2.setMinimum(self.spinBox_z1.value())

        self.display(True)


    def mouse_move(self, event):
        ax = event.inaxes
        if not ax:
            return

        x, y = int(event.xdata), int(event.ydata)
        if ax == self.pxy:
            HU = self.ct.voxel[self.spinBox_z0.value(), y, x]
            msg = 'x = {:d}, y = {:d}, z = {:d}, HU = {:d}'.format(x, y, self.spinBox_z0.value(), HU)
        elif ax == self.pxz:
            HU = self.ct.voxel[y, self.spinBox_y0.value(), x]
            msg = 'x = {:d}, y = {:d}, z = {:d}, HU = {:d}'.format(x, self.spinBox_y0.value(), y, HU)
        else:
            HU = self.ct.voxel[y, x, self.spinBox_x0.value()]
            msg = 'x = {:d}, y = {:d}, z = {:d}, HU = {:d}'.format(self.spinBox_x0.value(), x, y, HU)

        self.statusBar.showMessage(msg)


    def display(self, enforce_refresh=False):
        if not self.hold_display_refresh or enforce_refresh:
            self.hold_display_refresh = False
            if self.firstDraw:
                self.pxy = self.fig.add_subplot(1, 2, 1)
                self.pxz = self.fig.add_subplot(2, 2, 2)
                self.pyz = self.fig.add_subplot(2, 2, 4)
                self.firstDraw = False
            else:
                self.pxy.clear()
                self.pxz.clear()
                self.pyz.clear()

            x0 = self.spinBox_x0.value()
            y0 = self.spinBox_y0.value()
            z0 = self.spinBox_z0.value()
            self.pxy.imshow(self.ct.voxel[z0,:,:], cmap='gray', aspect=self.ct.dy/self.ct.dx)
            self.pxz.imshow(self.ct.voxel[:,y0,:], cmap='gray', aspect=self.ct.dz/self.ct.dx)
            self.pyz.imshow(self.ct.voxel[:,:,x0], cmap='gray', aspect=self.ct.dz/self.ct.dy)

            self.pxy.set_xlabel('X')
            self.pxy.set_ylabel('Y')
            self.pxy.set_title('Z = {:d}'.format(self.spinBox_z0.value()))
            
            self.pxz.set_xlabel('X')
            self.pxz.set_ylabel('Z')
            self.pxz.set_title('Y = {:d}'.format(self.spinBox_y0.value()))

            self.pyz.set_xlabel('Y')
            self.pyz.set_ylabel('Z')
            self.pyz.set_title('X = {:d}'.format(self.spinBox_x0.value()))
            
            # draw display center lines
            if self.checkBox_center_lines.isChecked():
                color = 'white'
                self.pxy.plot([0, self.ct.nx-1], [y0, y0], color=color, linestyle='--')
                self.pxy.plot([x0, x0], [0, self.ct.ny-1], color=color, linestyle='--')
                self.pxz.plot([0, self.ct.nx-1], [z0, z0], color=color, linestyle='--')
                self.pxz.plot([x0, x0], [0, self.ct.nz-1], color=color, linestyle='--')
                self.pyz.plot([0, self.ct.ny-1], [z0, z0], color=color, linestyle='--')
                self.pyz.plot([y0, y0], [0, self.ct.nz-1], color=color, linestyle='--')

            # draw cut lines
            cutcol = 'cyan'
            x1 = self.spinBox_x1.value()
            x2 = self.spinBox_x2.value()
            y1 = self.spinBox_y1.value()
            y2 = self.spinBox_y2.value()
            z1 = self.spinBox_z1.value()
            z2 = self.spinBox_z2.value()
            self.pxy.plot([x1, x2], [y1, y1], color=cutcol, linestyle=':')
            self.pxy.plot([x1, x2], [y2, y2], color=cutcol, linestyle=':')
            self.pxy.plot([x1, x1], [y1, y2], color=cutcol, linestyle=':')
            self.pxy.plot([x2, x2], [y1, y2], color=cutcol, linestyle=':')
            self.pxz.plot([x1, x2], [z1, z1], color=cutcol, linestyle=':')
            self.pxz.plot([x1, x2], [z2, z2], color=cutcol, linestyle=':')
            self.pxz.plot([x1, x1], [z1, z2], color=cutcol, linestyle=':')
            self.pxz.plot([x2, x2], [z1, z2], color=cutcol, linestyle=':')
            self.pyz.plot([y1, y2], [z1, z1], color=cutcol, linestyle=':')
            self.pyz.plot([y1, y2], [z2, z2], color=cutcol, linestyle=':')
            self.pyz.plot([y1, y1], [z1, z2], color=cutcol, linestyle=':')
            self.pyz.plot([y2, y2], [z1, z2], color=cutcol, linestyle=':')

            # draw dose when exists
            if self.with_dose:
                levels = [0.02, 0.1, 1, 10, 100]
                self.pxy.contourf(self.ct.dose_pct[z0,:,:], levels=levels, norm=LogNorm(), cmap='jet', alpha=0.5)
                self.pxz.contourf(self.ct.dose_pct[:,y0,:], levels=levels, norm=LogNorm(), cmap='jet', alpha=0.5)
                self.pyz.contourf(self.ct.dose_pct[:,:,x0], levels=levels, norm=LogNorm(), cmap='jet', alpha=0.5)

            plt.tight_layout()
            self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = myApp()
    window.show()
    sys.exit(app.exec_())
