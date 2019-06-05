import sys

sys.path.append("/nfs/paper-big-data-engines")

import argparse
from io import BytesIO
import os
from time import time

import dask
import dask.array as da
from dask.distributed import Client
import nibabel as nib

from utils import benchmark, crawl_dir


def get_voxels(filename, start, args):
    """Retrieve voxel intensity of a Nifti image as a byte stream.

    Parameters
    ----------
    filename: str
        Representation of the path for the input file.

    Returns
    -------
    data : da.array
        Data of the nifti imaeg read.
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
            get_voxels.__name__,
        )

    return da.from_array(data)


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
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    # Allow workers to use module
    client.upload_file("/nfs/paper-big-data-engines/utils.py")
    client.upload_file("/nfs/paper-big-data-engines/kmeans/Kmeans.py")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))

    img = [get_voxels(path, start=start, args=args) for path in paths]
    voxels = da.concatenate(img).reshape(-1)

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

    start_time = time() - start

    with open(f"{args.output_dir}/histogram.csv", "w") as f_out:
        for x in zip(unique, counts):
            f_out.write(f"{x[0]};{x[1]}\n")

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            "all_file",
            args.output_dir,
            args.experiment,
            "save_histogram",
        )
