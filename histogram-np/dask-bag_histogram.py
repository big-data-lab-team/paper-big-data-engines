import argparse
import os
import sys
from time import time

import dask.bag as db
from dask.distributed import Client

sys.path.append("/nfs/paper-big-data-engines/histogram")


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
    client.upload_file("/nfs/paper-big-data-engines/histogram/Histogram.py")
    from utils import benchmark, crawl_dir, read_img
    from Histogram import (
        calculate_histogram,
        combine_histogram,
        flatten,
        save_histogram,
    )

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = db.from_sequence(paths, npartitions=len(paths))
    img = paths.map(lambda p: read_img(p, start=start, args=args))

    img = img.map(lambda x: flatten(x[1], start=start, args=args, filename=x[0]))

    partial_histogram = img.map(
        lambda x: calculate_histogram(x[1], args=args, start=start, filename=x[0])
    )

    histogram = partial_histogram.fold(
        lambda x, y: combine_histogram(x, y, args=args, start=start)
    ).compute()

    save_histogram(histogram, args=args, start=start)
