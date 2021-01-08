from functools import reduce
import glob
import os
import time

import numpy as np
from pyspark import SparkConf, SparkContext

from ..commons.histogram import (
    calculate_histogram,
    combine_histogram,
    flatten,
    save_histogram,
)
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    benchmark: bool,
) -> None:
    experiment = f"spark:histogram"
    start_time = time.time()
    common_args = {
        "benchmark": benchmark,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    conf = SparkConf().setMaster(scheduler).setAppName(experiment)
    sc = SparkContext.getOrCreate(conf=conf)

    filenames = glob.glob(input_folder + "/*.nii")
    paths = sc.parallelize(filenames, len(filenames))
    img_rdd = paths.map(lambda p: load(p, **common_args))

    img_rdd = img_rdd.map(lambda x: flatten(x[1], filename=x[0], **common_args))

    partial_histogram = img_rdd.map(
        lambda x: calculate_histogram(x[1], filename=x[0], **common_args)
    )

    histogram = partial_histogram.fold(
        np.array([0] * (2 ** 16 - 1)),
        lambda x, y: combine_histogram(x, y, **common_args),
    )

    save_histogram(histogram, **common_args)
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )