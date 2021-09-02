# Reference: https://gist.github.com/ofgulban/46d5c51ea010611cbb53123bb5906ca9
import glob
import os
import sys

from nibabel import load, save, Nifti1Image
import numpy as np

input_folder = sys.argv[1]

for filename in glob.glob(input_folder + "/*.mnc"):
    minc = load(filename)
    basename = minc.get_filename().split(os.extsep, 1)[0]

    affine = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]])

    out = Nifti1Image(minc.get_data(), affine=affine)
    save(out, basename + ".nii")
