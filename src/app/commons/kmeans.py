import os
import time

import nibabel as nib
import numpy as np
import numexpr as ne

from ..utils import log


def eucledian_distance(arr: np.array, c: float):
    """Returns the eucledian distance between x and y.

    Parameters
    ----------
    arr : float
        1-D array of voxel
    c : float
        centroid

    Returns
    -------
        The Eucledian distance between x and y.
    """
    # TODO benchmark
    return np.linalg.norm(arr[:, None] - c, axis=-1)


def closest_centroids(x, centroids):
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
    # TODO benchmark

    dist = np.array([eucledian_distance(x, c) for c in centroids])
    return dist.T.argmin(1)


def classify_block(block, centroids):
    filename = block[0]
    img = block[1]
    metadata = block[2]

    img = np.array([np.absolute(img - centroid) for centroid in centroids]).argmin(0)
    # TODO benchmark

    return filename, img, metadata


def dump(img_rdd, *, benchmark, start, output_folder, experiment):
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

    # save classified image
    bn = os.path.basename(filename)
    f_out = os.path.join(output_folder, f"classified-{bn}")
    classified_img = nib.Nifti1Image(img, metadata[0], header=metadata[1])
    nib.save(classified_img, f_out)

    end_time = time.time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            filename,
            output_folder,
            experiment,
            dump.__name__,
        )

    return f_out, "SUCCESS"
