import glob
import os
import time

from pyspark import SparkConf, SparkContext

from ..commons.increment import increment, dump
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_worker: int,
    benchmark_folder: str,
    *,
    block_size: int,
    iterations: int,
    delay: int,
) -> None:
    experiment = f"spark:increment:{n_worker=}:{block_size=}:{iterations=}:{delay=}"
    start_time = time.time()
    common_args = {
        "benchmark_folder": benchmark_folder,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    if scheduler.lower() == "slurm":
        scheduler = os.environ["MASTER_URL"]

    conf = SparkConf().setMaster(scheduler).setAppName(experiment)
    sc = SparkContext.getOrCreate(conf=conf)

    filenames = glob.glob(input_folder + "/*.nii")
    paths = sc.parallelize(filenames, len(filenames))
    img_rdd = paths.map(lambda p: load(p, **common_args))

    for _ in range(iterations):
        img_rdd = img_rdd.map(lambda x: increment(x, delay=delay, **common_args))

    img_rdd = img_rdd.map(lambda x: dump(x, **common_args))

    img_rdd.collect()

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
