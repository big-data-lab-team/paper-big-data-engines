import argparse
from time import time
import os

from pyspark import SparkConf, SparkContext

from Increment import increment, save_results
from utils import crawl_dir, read_img


if __name__ == "__main__":

    start = time()  # Start time of the pipeline

    parser = argparse.ArgumentParser(description="BigBrain incrementation")
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
        "delay", type=float, help="sleep delay during " "incrementation"
    )
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    conf = SparkConf().setAppName("Spark Incrementation")
    sc = SparkContext.getOrCreate(conf=conf)

    sc.addFile("/nfs/paper-big-data-engines/utils.py")
    sc.addFile("/nfs/paper-big-data-engines/incrementation/Increment.py")
    print("Connected")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = sc.parallelize(paths, len(paths))
    img_rdd = paths.map(lambda p: read_img(p, start=start, args=args))

    # Increment the data n time:
    for _ in range(args.iterations):
        img_rdd = img_rdd.map(
            lambda x: increment(x, delay=args.delay, start=start, args=args)
        )

    # Save the data
    img_rdd = img_rdd.map(lambda x: save_results(x, start=start, args=args))

    img_rdd.collect()
