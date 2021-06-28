import os
import time

import nibabel as nib
import numpy as np

from ..utils import log


def closest_centroids(x, centroids, *, benchmark_folder, start, experiment, **kwargs):
    """Returns the index of the closest centroids.

    Parameters
    ----------
    x : np.array
        1-D array of voxels.
    centroids : list(T)
        List of current centroids.

    Returns
    -------
    closest_centroid : T
    """
    start_time = time.time() - start

    rv = np.argmin([np.absolute(x - c) for c in centroids], axis=0)

    end_time = time.time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            "all",
            benchmark_folder,
            experiment,
            closest_centroids.__name__,
        )

    return rv


def classify_block(block, centroids, *, benchmark_folder, start, experiment, **kwargs):
    start_time = time.time() - start

    filename = block[0]
    img = block[1]
    metadata = block[2]

    img = np.argmin(np.fabs(np.subtract.outer(img, centroids)), axis=0)

    end_time = time.time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            filename,
            benchmark_folder,
            experiment,
            classify_block.__name__,
        )

    return filename, img, metadata


def dump(img_rdd, *, benchmark_folder, start, output_folder, experiment, **kwargs):
    """Save a Nifti image.

    Parameters
    ----------
    img_rdd: (str, np.array, (np.array, np.array))
        Filename, image, and image header and affine.
    assignment: (float, (int, int))
        Voxel's class, intensity and frequency.
    start : float
        Start time of the application.
    args : {str: Any}
        Runtime arguments of the application.

    Returns
    -------
    f_out : str
        Output path where the image is saved.
    "SUCCESS" : str
        Indicates that the pipeline succeeded.
    """
    start_time = time.time() - start

    filename = img_rdd[0]
    img = img_rdd[1]
    metadata = img_rdd[2]

    bn = os.path.basename(filename)
    f_out = os.path.join(output_folder, f"classified-{bn}")

    classified_img = nib.Nifti1Image(img, metadata[0], header=metadata[1])
    nib.save(classified_img, f_out)

    end_time = time.time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            filename,
            benchmark_folder,
            experiment,
            dump.__name__,
        )

    return f_out, "SUCCESS"
