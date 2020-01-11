import numpy as np
import os
import struct
import pydicom
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
from matplotlib.colors import LogNorm

class ct_img:
    def __init__(self, prefix='ct'):
        self.nx = self.ny = self.nz = 0
        self.dx = self.dy = self.dz = np.float32(0.0)
        self.prefix = prefix
        self.havedose = False
        return

    def __init__(self, ct_input, prefix='ct'):
        self.prefix = prefix
        self.havedose = False
        if os.path.isdir(ct_input):     # combine dicom files into a single img file
            self.dir = ct_input
            self.dicom2img(ct_input)
        elif os.path.isfile(ct_input):  # read processed img file
            self.dir = os.path.dirname(ct_input)
            self.read_img(ct_input)
        else:
            raise Exception('Cannot find {:}'.format(ct_input))
        return

    def dicom2img(self, ct_dir):
        os.chdir(ct_dir)
        files = [f for f in os.listdir('.') if f.endswith('.dcm')]

        # sort DICOM files accodring to slice locations
        file_z = []
        for f in files:
            ds = pydicom.dcmread(f)
            z = float(ds.SliceLocation)
            file_z.append((f, z))
        files = [f[0] for f in sorted(file_z, key=lambda tuple: tuple[1])]
        self.nx = ds.Columns
        self.ny = ds.Rows
        self.nz = len(files)
        self.dx, self.dy = np.array(ds.PixelSpacing, dtype=np.float32)
        self.dz = np.float32(ds.SliceThickness)

        # read files as order to combine them into one 3D array
        self.voxel = np.zeros((self.nz, self.ny, self.nx), dtype=np.int16)
        for i in range(self.nz):
            ds = pydicom.dcmread(files[i])
            self.voxel[i,:,:] = ds.pixel_array

        return


    def voxel_info(self):
        info = '({:d}, {:d}, {:d}) voxels with ({:.3f}, {:.3f}, {:.3f}) mm size'.format(self.nx, self.ny, self.nz, self.dx, self.dy, self.dz)
        return info


    def read_img(self, img_file):
        with open(img_file, 'rb') as f:
            self.nx, self.ny, self.nz = struct.unpack('iii', f.read(12))
            self.dx, self.dy, self.dz = struct.unpack('fff', f.read(12))
            self.voxel = np.fromfile(f, dtype=np.int16, count=self.nx*self.ny*self.nz).reshape(self.nz, self.ny, self.nx)
        return


    def write_img(self, img_file):
        with open(img_file, 'wb') as f:
            f.write(struct.pack('iii', self.nx, self.ny, self.nz))
            f.write(struct.pack('fff', self.dx, self.dy, self.dz))
            f.write(self.voxel.tobytes())
            f.close()
        return


    def read_dose(self, dose_file, verbose=False):
        with open(dose_file, 'rb') as f:
            nx, ny, nz = struct.unpack('iii', f.read(12))
            dx, dy, dz = struct.unpack('fff', f.read(12))
            if(nx != self.nx or ny != self.ny or nz != self.nz or dx != self.dx or dy != self.dy or dz !=self.dz):
                print('Image: ({:d}, {:d}, {:d}) at ({:.3f}, {:.3f}, {:.3f}) mm'.format(self.nx, self.ny, self.nz, self.dx, self.dy, self.dz))
                print('Dose:  ({:d}, {:d}, {:d}) at ({:.3f}, {:.3f}, {:.3f}) mm'.format(nx, ny, nz, dx, dy, dz))
                raise Exception('Error: the image and dose voxels do not match.')
            self.dose_x, self.dose_z, self.dose_e = struct.unpack('iif', f.read(12))
            self.dose_x0, self.dose_x1 = struct.unpack('ii', f.read(8))
            self.dose_z0, self.dose_z1 = struct.unpack('ii', f.read(8))
            dose_nx = self.dose_x1 - self.dose_x0 + 1
            dose_nz = self.dose_z1 - self.dose_z0 + 1
            if verbose:
                print('Dose at X = {:d}, Z = {:d}, Energy = {:.2f}'.format(self.dose_x, self.dose_z, self.dose_e))
                print('Dose range is X({:d}, {:d}), Z({:d}, {:d})'.format(self.dose_x0, self.dose_x1, self.dose_z0, self.dose_z1))
            self.dose = np.zeros_like(self.voxel, dtype=np.float32)
            self.dose[self.dose_z0:self.dose_z1+1,:,self.dose_x0:self.dose_x1+1] = np.fromfile(f, dtype=np.float32, count=dose_nx*self.ny*dose_nz).reshape(dose_nz, self.ny, dose_nx)
            self.dose_pct = self.dose / (self.dose.max() * 0.01)
            self.havedose = True
        return


    def polt3views(self, ix=None, iy=None, iz=None, showdose=True, savefig=False):
        if ix == None:
            ix = self.nx // 2
        if iy == None:
            iy = self.ny // 2
        if iz == None:
            iz = self.nz // 2

        os.chdir(self.dir)

        X = Y = self.nx * self.dx
        Z = self.nz * self.dz
        pad = 0.03

        x = y = (1. - pad * 3) * X / (X + Z)
        z = (1. - pad * 3) * Z / (X + Z)
        xy = [pad, pad, x, y]
        xz = [pad, y + pad * 2, x, z]
        zy = [x + pad * 2, pad, z, y]

        plt.figure(1, figsize=(3,3), dpi=200, facecolor='white')
        pxy = plt.axes(xy)
        pxz = plt.axes(xz)
        pzy = plt.axes(zy)
        
        pxy.imshow(self.voxel[iz,:,:], cmap='gray')
        pxz.imshow(self.voxel[:,iy,:], cmap='gray', aspect=self.dz/self.dx)
        pzy.imshow(self.voxel[:,:,ix].transpose(), cmap='gray', aspect=self.dy/self.dz)

        if showdose and self.havedose:
            levels = [0.02, 0.1, 1, 10, 100]
            pxy.contourf(self.dose_pct[iz,:,:], levels=levels, norm=LogNorm(), cmap='jet', alpha=0.5)
            pxz.contourf(self.dose_pct[:,iy,:], levels=levels, norm=LogNorm(), cmap='jet', alpha=0.5)
            pzy.contourf(self.dose_pct[:,:,ix].transpose(), levels=levels, norm=LogNorm(), cmap='jet', alpha=0.5)
        
        nullfmt = NullFormatter()
        pxz.xaxis.set_major_formatter(nullfmt)
        pzy.yaxis.set_major_formatter(nullfmt)
        pxz.set_xlim(pxy.get_xlim())
        pzy.set_ylim(pxy.get_ylim())
        pxy.set_axis_off()
        pxz.set_axis_off()
        pzy.set_axis_off()

        if savefig:
            plt.savefig(self.prefix + '_{:}-{:}-{:}.png'.format(ix, iy, iz))
        plt.show()
        return
