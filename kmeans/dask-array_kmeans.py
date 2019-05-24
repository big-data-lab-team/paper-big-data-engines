import argparse
from io import BytesIO
import os
from time import time

import dask
import dask.array as da
from dask.distributed import Client
import nibabel as nib
import numpy as np

from Kmeans import eucledian_distance
from utils import benchmark, crawl_dir


def read_img(filename, start, args):
    """Read a Nifti image as a byte stream.

    Parameters
    ----------
    filename: str
        Representation of the path for the input file.

    Returns
    -------
    filename : str
        Representation of the path for the input file.
    data : da.array
        Data of the nifti imaeg read.
    (img.affine, img.header) : (np.array, np.array)
        Affine and header of the nifti image read.
    """
    start_time = time() - start

    img = None
    with open(filename, "rb") as f_in:
        fh = nib.FileHolder(fileobj=BytesIO(f_in.read()))
        img = nib.Nifti1Image.from_file_map({"header": fh, "image": fh})
    data = img.get_data()

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            read_img.__name__,
        )

    return filename, da.from_array(data), (img.affine, img.header)


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
        dist = eucledian_distance(x, centroid)

        if dist < min_dist:
            min_dist = dist
            closest_centroid = centroid

    return closest_centroid


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
            map(lambda x: x[1], filter(lambda x: x[0] == class_, assignments))
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


if __name__ == "__main__":

    start = time()  # Start time of the pipeline

    parser = argparse.ArgumentParser(description="BigBrain Kmeans")
    parser.add_argument("scheduler", type=str, help="Scheduler ip and port")
    parser.add_argument(
        "bb_dir",
        type=str,
        help=("The folder containing BigBrain NIfTI images" "(local fs only)"),
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help=("the folder to save incremented images to" "(local fs only)"),
    )
    parser.add_argument(
        "experiment", type=str, help="Name of the experiment being performed"
    )
    parser.add_argument("iterations", type=int, help="number of iterations")
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    client.upload_file("nfs/SOEN-499-Project/utils.py")  # Allow workers to use module
    client.upload_file("nfs/SOEN-499-Project/kmeans/Kmeans.py")

    # Read images
    paths = crawl_dir(os.path.abspath("test/data"))

    img = [read_img(path, start=start, args=args) for path in paths]

    voxels = da.concatenate([x[1] for x in img]).reshape(-1)

    centroids = [0.0, 125.8, 251.6, 377.4]  # Initial centroids
    voxel_pair = None

    bincount = da.bincount(voxels)
    bincount = bincount[bincount != 0]
    unique = da.unique(voxels)

    unique, counts = dask.compute(unique, bincount)

    for i in range(0, args.iterations):  # Disregard convergence.
        start_time = time() - start

        associated_centroid = np.array(
            np.vectorize(closest_centroid, excluded=["centroids"])(
                x=unique, centroids=centroids
            )
        )

        unique_total = unique * counts

        # Find centroid (total, count) => total/count = centroid
        centroids = np.array(
            [unique_total[associated_centroid == k].sum() for k in centroids]
        ) / np.array([counts[associated_centroid == k].sum() for k in centroids])

        end_time = time() - start

        if args.benchmark:
            benchmark(
                start_time,
                end_time,
                "all_file",
                args.output_dir,
                args.experiment,
                "update_centroids",
            )

    voxel_pair = np.vstack(associated_centroid, unique).T

    for x in img:
        save_results(x, voxel_pair, start=start, args=args).compute()
