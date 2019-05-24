import argparse
from io import BytesIO
import os
from time import time

import dask
import dask.array as da
from dask.distributed import Client, LocalCluster
import nibabel as nib
import numpy as np

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
    # cluster = args.scheduler
    cluster = LocalCluster(n_workers=2)
    client = Client(cluster)

    print(client)
    # client.upload_file("nfs/SOEN-499-Project/utils.py")  # Allow workers to use module
    # client.upload_file("nfs/SOEN-499-Project/kmeans/Kmeans.py")

    # Read images
    paths = crawl_dir(os.path.abspath("test/data"))

    img = [read_img(path, start=start, args=args) for path in paths]
    voxels = da.concatenate([x[1] for x in img]).reshape(-1)

    start_time = time() - start

    bincount = da.bincount(voxels)
    bincount = bincount[bincount != 0]
    unique = da.unique(voxels)

    unique, counts = dask.compute(unique, bincount)

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            "all_file",
            args.output_dir,
            args.experiment,
            "find_frequency",
        )

