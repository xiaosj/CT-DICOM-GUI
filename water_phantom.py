# Generate a pseudo water phantom
import numpy as np
from ct_image import ct_img

phantom = ct_img()
phantom.nx = phantom.ny = phantom.nz = 100
phantom.dx = phantom.dy = phantom.dz = 1.0
phantom.voxel = np.zeros((phantom.nx, phantom.ny, phantom.nz))
phantom.write_img('water_100_1mm.img')
