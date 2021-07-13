import glob
import os
import time
import uuid

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
    n_worker: int,
    benchmark_folder: str,
    *,
    block_size: int,
) -> None:
    experiment = os.path.join(
        f"spark:histogram:{n_worker=}:{block_size=}", str(uuid.uuid1())
    )

    if scheduler.lower() == "slurm":
        scheduler = os.environ["MASTER_URL"]

    conf = SparkConf().setMaster(scheduler).setAppName(experiment)
    conf.set("spark.driver.maxResultSize", "4g")
    sc = SparkContext.getOrCreate(conf=conf)

    start_time = time.time()
    common_args = {
        "benchmark_folder": benchmark_folder,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

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

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
