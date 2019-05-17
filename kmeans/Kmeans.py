import sys

sys.path.append("/nfs/SOEN-499-Project")

import math
import os
from time import time

import nibabel as nib
import numpy as np

from utils import benchmark


def eucledian_distance(xs, ys):
    """Returns the eucledian distance between x and y.

    Parameters
    ----------
    xs : float or [float]
        Data point.
    ys : float or [float]
        Data point.

    Returns
    -------
    filename : str
        Name of the file being processed.
    dist : [float]
        The Eucledian distance between x and y.
    """
    # Operate on vector only for generality
    xs = xs if isinstance(xs, list) or isinstance(xs, tuple) else [xs]
    ys = ys if isinstance(ys, list) or isinstance(ys, tuple) else [ys]

    dist = list()
    assert len(xs) == len(ys)
    for x, y in zip(xs, ys):
        for ops in ["__add__", "__sub__", "__pow__"]:
            assert (
                ops in type(x).__dict__
            ), f"{type(x)} does not have {ops} thus the distance cannot be calculated."
            assert (
                ops in type(y).__dict__
            ), f"{type(y)} does not have {ops} thus the distance cannot be calculated."

        dist.append((x - y) ** 2)

    return math.sqrt(sum(dist))


def closest_centroid(x, centroids):
    """Returns the closest centroids to point x.

    Parameters
    ----------
    x : T
        Data point to cluster.
    centroids : list(T)
        List of current centroids.

    Returns
    -------
    closest_centroid : T
        Centroids closest to point x.
    """

    min_dist = float("inf")
    closest_centroid = None

    for centroid in centroids:
        dist = eucledian_distance(x[0], centroid)

        if dist < min_dist:
            min_dist = dist
            closest_centroid = centroid

    assert isinstance(closest_centroid, float)
    return closest_centroid, x


def add_component_wise(total, x):
    """Binary operator to reduce

    Parameters
    ----------
    total : (float, int)
        Total value of the combination and number of element combined to obtain it.
    x : int, (float, int)
        Total value of the combination and number of element combined to obtain it.
    """
    return total[0] + x[0], (total[1][0] + x[1][0], total[1][1] + x[1][1])


def get_voxels(voxels):
    """Return the list of voxels for the NiftiImage.

    Parameters
    ----------
    voxels : 2D np.array
        Voxels from the nifti image.

    Returns
    -------
    np.array
        The list of voxels for the NiftiImage.
    """

    return voxels.flatten("F")


def save_results(img_rdd, assignments, *, start, args):
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
    start_time = time() - start
    filename = img_rdd[0]
    img = img_rdd[1]
    metadata = img_rdd[2]

    assigned_class = {class_[0] for class_ in assignments}

    for class_ in assigned_class:
        assigned_voxels = list(
            map(lambda x: x[1][0], filter(lambda x: x[0] == class_, assignments))
        )
        img[np.where(np.isin(img, assigned_voxels))] = class_

    bn = os.path.basename("classified-" + filename[:-3] + "nii")  # Save in nifti format
    f_out = os.path.join(args.output_dir, "images/" + bn)

    # save classified image
    classified_img = nib.Nifti1Image(img, metadata[0], header=metadata[1])
    nib.save(classified_img, f_out)

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
