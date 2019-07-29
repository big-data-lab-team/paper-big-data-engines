import argparse
import os
import sys
from time import time

import numpy as np
from pyspark import SparkConf, SparkContext

sys.path.append("/nfs/paper-big-data-engines/histogram")


if __name__ == "__main__":

    start = time()  # Start time of the pipeline

    parser = argparse.ArgumentParser(description="BigBrain Kmeans")
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
    conf = SparkConf().setAppName(f"Spark {args.experiment}")
    sc = SparkContext.getOrCreate(conf=conf)

    sc.addFile("/nfs/paper-big-data-engines/utils.py")
    sc.addFile("/nfs/paper-big-data-engines/histogram/Histogram.py")
    from utils import benchmark, crawl_dir, read_img
    from Histogram import (
        calculate_histogram,
        combine_histogram,
        flatten,
        save_histogram,
    )

    print("Connected")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = sc.parallelize(paths, len(paths))
    img_rdd = paths.map(lambda p: read_img(p, start=start, args=args))

    img_rdd = img_rdd.map(
        lambda x: flatten(x[1], start=start, args=args, filename=x[0])
    )

    partial_histogram = img_rdd.map(
        lambda x: calculate_histogram(x[1], args=args, start=start, filename=x[0])
    )

    histogram = partial_histogram.fold(
        np.array([0] * (2**16 - 1)),
        lambda x, y: combine_histogram(x, y, args=args, start=start),
    )

    save_histogram(histogram, args=args, start=start)
