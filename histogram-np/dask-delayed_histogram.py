import argparse
from functools import reduce
import os
import sys
from time import time

import dask
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

    partial_histogram = []
    for path in paths:
        img = dask.delayed(read_img)(path, start=start, args=args)

        img = dask.delayed(flatten)(img[1], start=start, args=args, filename=img[0])

        partial_histogram.append(
            dask.delayed(calculate_histogram)(
                img[1], args=args, start=start, filename=img[0]
            )
        )

    histogram = dask.delayed(reduce)(
        lambda x, y: combine_histogram(x, y, args=args, start=start), partial_histogram
    )

    future = client.compute(histogram)
    histogram = client.gather(future)

    save_histogram(histogram, args=args, start=start)

    client.close()
