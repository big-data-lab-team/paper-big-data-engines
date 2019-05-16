import sys

sys.path.append("/nfs/SOEN-499-Project")

import os
from time import time, sleep

import nibabel as nib

from utils import benchmark


def increment(img_rdd, delay, start, args):
    """Increment the data of a Nifti image by 1.

    :param filename: str -- representation of the path for the input file.
    :param data: nifti1Image -- image to manipulate.
    :param metadata: tuple -- of the form (image affine, image header).
    :param delay: int -- sleep time for the task
    :return: tuple -- of the form (filename, data, (image affine,
    image header), iteration+1).
    """
    start_time = time() - start

    filename = img_rdd[0]
    data = img_rdd[1]
    metadata = img_rdd[2]

    data += 1
    sleep(delay)

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            increment.__name__,
        )

    return filename, data, metadata


def save_results(img_rdd, start, args):
    """Save a Nifti image.

    Parameters
    ----------
    img_rdd: (str, np.array, (np.array, np.array))
        Filename, image, and image header and affine.

    Returns
    -------
    f_out : str
        Output path where the image is saved.
    "SUCCESS" : str
        Indicates that the pipeline succeeded.
    """
    start_time = time() - start

    filename = img_rdd[0]
    data = img_rdd[1]
    metadata = img_rdd[2]

    bn = os.path.basename(filename[:-3] + "nii")  # Save in nifti format
    f_out = os.path.join(args.output_dir, "images/" + bn)

    img = nib.Nifti1Image(data, metadata[0], header=metadata[1])
    nib.save(img, f_out)

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            save_results.__name__,
        )

    return f_out, "SUCCESS"
