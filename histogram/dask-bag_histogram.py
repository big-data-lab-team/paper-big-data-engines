import argparse
import os
from time import time

import dask.bag as db
from dask.distributed import Client, LocalCluster

from utils import benchmark, crawl_dir, read_img


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
    # client.upload_file("/nfs/SOEN-499-Project/utils.py")  # Allow workers to use module
    # client.upload_file("/nfs/SOEN-499-Project/kmeans/Kmeans.py")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = db.from_sequence(paths, npartitions=len(paths))
    img_rdd = paths.map(lambda p: read_img(p, start=start, args=args))

    start_time = time() - start

    voxels = img_rdd.map(lambda x: x[1].flatten("F")).flatten()
    frequency_pair = voxels.frequencies().compute()

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
