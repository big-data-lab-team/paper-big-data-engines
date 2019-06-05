import sys

sys.path.append("/nfs/paper-big-data-engines")

import argparse
import os
from time import time

from pyspark import SparkConf, SparkContext

from utils import benchmark, crawl_dir, read_img


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
    conf = SparkConf().setAppName("Spark Incrementation")
    sc = SparkContext.getOrCreate(conf=conf)

    sc.addFile("/nfs/paper-big-data-engines/utils.py")
    sc.addFile("/nfs/paper-big-data-engines/kmeans/Kmeans.py")
    print("Connected")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = sc.parallelize(paths, len(paths))
    img_rdd = paths.map(lambda p: read_img(p, start=start, args=args))

    start_time = time() - start

    voxels = img_rdd.flatMap(lambda x: x[1].flatten("F"))
    frequency_pair = (
        voxels.map(lambda x: (x, 1)).reduceByKey(lambda x, y: x + y).collect()
    )

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
        for x in frequency_pair:
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
