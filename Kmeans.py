from io import BytesIO
import math
from time import time

import nibabel as nib

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
