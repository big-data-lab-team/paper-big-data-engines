import sys

sys.path.append("/nfs/SOEN-499-Project")

import argparse
from functools import reduce
import os
from time import time

import dask
from dask.distributed import Client

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
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    # Allow workers to use module
    client.upload_file("/nfs/SOEN-499-Project/utils.py")
    client.upload_file("/nfs/SOEN-499-Project/kmeans/Kmeans.py")

    def calculate_histogram(arr):
        start_time = time() - start

        histogram = dict()
        for x in arr:
            if x not in histogram:
                histogram[x] = 0
            histogram[x] += 1

        end_time = time() - start

        if args.benchmark:
            benchmark(
                start_time,
                end_time,
                "all_file",
                args.output_dir,
                args.experiment,
                "calculate_histogram",
            )
        return histogram

    def combine_histogram(x, y):
        start_time = time() - start

        rv = {k: x.get(k, 0) + y.get(k, 0) for k in set(x) | set(y)}

        end_time = time() - start

        if args.benchmark:
            benchmark(
                start_time,
                end_time,
                "all_file",
                args.output_dir,
                args.experiment,
                "combine_histogram",
            )
        return rv

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))

    partial_histogram = []
    for path in paths:
        img_rdd = dask.delayed(read_img)(path, start=start, args=args)

        voxels = img_rdd[1].flatten("F")

        partial_histogram.append(dask.delayed(calculate_histogram)(voxels))

    histogram = dask.delayed(reduce)(
        lambda x, y: combine_histogram(x, y), partial_histogram
    )

    future = client.compute(histogram)
    histogram = client.gather(future)

    start_time = time() - start

    with open(f"{args.output_dir}/histogram.csv", "w") as f_out:
        for k, v in histogram.items():
            f_out.write(f"{k};{v}\n")

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

    client.close()
