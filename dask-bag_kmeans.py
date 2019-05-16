import argparse
import os
from time import time

import dask.bag as db
from dask.distributed import Client, LocalCluster
import nibabel as nib
import numpy as np

from Kmeans import add_component_wise, closest_centroid, get_voxels
from utils import benchmark, crawl_dir, read_img


def save_results(img_rdd, assignments, *, start, args):
    """Save a Nifti image.

    Parameters
    ----------
    filename: str
        Representation of the path for the input file.
    img_rdd: (str, np.array, (np.array, np.array))
        Filename, image, and image header and affine.
    metadata: (np.array, np.array)
        Affine and header of the image.
    start : float
        Start time of the application.
    args : {str: Any}

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
    parser.add_argument(
        "--k", nargs="?", const=4, type=int, help="Number of classes in the dataset"
    )
    parser.add_argument(
        "--seed", nargs="?", const=0, help="Seed to choose initial centroids"
    )
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    # Cluster scheduler
    # cluster = args.scheduler
    cluster = LocalCluster(
        n_workers=1, dashboard_address="127.0.0.1:8787"
    )  # TODO REMOVE for experiments
    client = Client(cluster)

    print(client)
    client.upload_file("utils.py")  # Allow workers to use module
    client.upload_file("Kmeans.py")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = db.from_sequence(paths, npartitions=len(paths))
    img_rdd = paths.map(lambda p: read_img(p, start=start, args=args)).persist()

    voxels = img_rdd.map(lambda x: get_voxels(x[1])).flatten()

    # Initial centroids
    centroids = [0.0, 125.8, 251.6, 377.4]

    voxel_pair = None
    for i in range(0, args.iterations):  # Disregard convergence.
        voxel_pair = voxels.frequencies().map(
            lambda x: (closest_centroid(x, centroids))
        )

        # Reduce voxel assigned to the same centroid together
        classe_pairs = (
            voxel_pair.map(lambda x: (x[0], (x[1][0] * x[1][1], x[1][1])))
            .foldby(0, add_component_wise, (0, (0, 0)))
            .map(lambda x: x[1][1])
            .compute()
        )
        # Find centroid (total, count) => total/count = centroid
        centroids = [pair[0] / pair[1] for pair in classe_pairs]

    voxel_pair = voxel_pair.compute()
    img_rdd.map(lambda x: save_results(x, voxel_pair, start=start, args=args)).compute()
