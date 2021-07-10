import glob
import os
import time
import uuid

from pyspark import SparkConf, SparkContext
import numpy as np

from ..commons.kmeans import classify_block, dump
from ..utils import load, log, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_worker: int,
    benchmark_folder: str,
    *,
    block_size: int,
    iterations,
) -> None:
    experiment = os.path.join(
        f"spark:kmeans:{n_worker=}:{block_size=}:{iterations=}", str(uuid.uuid1())
    )
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

    paths = sc.parallelize(glob.glob(input_folder + "/*.nii"))
    blocks = paths.map(lambda p: load(p, **common_args)).cache()
    voxels = (
        blocks.flatMap(lambda block: block[1])
        .flatMap(lambda block: block[1].flatten())
        .cache()
    )

    centroids = np.linspace(
        voxels.min(),
        voxels.max(),
        num=3,
    )

    for _ in range(iterations):  # Disregard convergence.
        start = time.time() - start_time

        centroids = np.array(
            voxels.map(lambda x: (np.argmin([abs(x - c) for c in centroids]), x))
            .aggregateByKey(
                (0, 0),
                lambda x, y: (
                    x[0] + y,
                    x[1] + 1,
                ),  # (runningSum, runningCount), nextValue
                lambda x, y: (x[0] + y[0], x[1] + y[1]),
            )
            .mapValues(lambda x: x[0] / x[1])
            .values()
            .collect(),
            dtype=np.uint16,
        )

        print(f"{centroids=}")

        end_time = time.time() - start_time

        if benchmark_folder:
            log(
                start,
                end_time,
                "all",
                benchmark_folder,
                experiment,
                "update_centroids",
            )

    blocks.map(lambda block: classify_block(block, centroids, **common_args)).map(
        lambda block: dump(
            block,
            **common_args,
        )
    ).collect()

    sc.stop()

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
