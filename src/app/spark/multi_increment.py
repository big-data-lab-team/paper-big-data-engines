import glob
import os
import random
import time
import uuid

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
    seed: int = 1234,
) -> None:
    experiment = os.path.join(
        f"spark:multi-increment:{n_worker=}:{block_size=}:{iterations=}:{delay=}:{seed=}",
        uuid.uuid1(),
    )
    start_time = time.time()
    common_args = {
        "benchmark_folder": benchmark_folder,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    conf = SparkConf().setMaster(scheduler).setAppName(experiment)
    sc = SparkContext.getOrCreate(conf=conf)

    filenames = glob.glob(input_folder + "/*.nii")
    paths = sc.parallelize(filenames, len(filenames))
    img_rdd = (
        paths.zipWithIndex().map(lambda x: (x[1], load(x[0], **common_args))).cache()
    )

    for _ in range(iterations):
        tmp = img_rdd.lookup(random.choice(range(len(filenames))))[0]
        img_rdd = img_rdd.map(
            lambda x: increment(
                x[1],
                delay=delay,
                increment_data=tmp,
                **common_args,
            )
        ).cache()

    img_rdd = img_rdd.map(lambda x: dump(x[1], **common_args))

    img_rdd.collect()

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
