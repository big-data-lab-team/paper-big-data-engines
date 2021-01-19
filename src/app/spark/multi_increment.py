import glob
import random
import time

from pyspark import SparkConf, SparkContext

from ..commons.increment import increment, dump
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_workers: int,
    benchmark: bool,
    *,
    iterations: int,
    delay: int,
    seed: int = 1234,
) -> None:
    experiment = (
        f"spark:multi-increment:iterations={iterations}:delay={delay}:seed={seed}"
    )
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

    for _ in range(iterations):
        img_rdd = img_rdd.map(
            lambda x: increment(
                x, delay=delay, increment_data=random.choice(img_rdd)[1], **common_args
            )
        )

    img_rdd = img_rdd.map(lambda x: dump(x, **common_args))

    img_rdd.collect()
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )