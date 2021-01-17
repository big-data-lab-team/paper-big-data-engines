import glob
import time

from pyspark import SparkConf, SparkContext
import numpy as np

from ..commons.kmeans import classify_block, closest_centroids, dump
from ..utils import load, log, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    benchmark: bool,
    *,
    iterations,
) -> None:
    experiment = f"spark:kmeans:iterations={iterations}"
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
    blocks = paths.map(lambda p: load(p, **common_args))
    voxels = blocks.flatMap(lambda block: block[1].flatten("F"))

    # Pick random initial centroids
    # TODO benchmark
    centroids = np.linspace(
        0,
        2 ** 16,
        # voxels.min().collect(),
        # voxels.max().collect(),
        num=3,
    )
    # centroids = voxels.takeSample(False, 3)
    print(centroids)

    for _ in range(0, iterations):  # Disregard convergence.
        start = time.time() - start_time

        centroid_index = voxels.mapPartitions(
            lambda chunk: closest_centroids(np.fromiter(chunk, np.float64), centroids)
        )

        print(f"calculated closest centroid in: {start - time.time()} seconds")

        # Reference: https://stackoverflow.com/a/29930162/11337357
        centroids = np.array(
            centroid_index.zip(voxels)
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
            .collect()
        )

        print(f"{centroids=}")

        end_time = time.time() - start

        if benchmark:
            log(
                start,
                end_time,
                "all_file",
                output_folder,
                experiment,
                "update_centroids",
            )

    blocks.map(lambda block: classify_block(block, centroids)).map(
        lambda block: dump(
            block,
            **common_args,
        )
    ).collect()

    sc.stop()
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )
