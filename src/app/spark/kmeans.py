import glob
import math
import os
import time
import uuid

from pyspark import SparkConf, SparkContext
import numpy as np

from ..commons.kmeans import classify_block, dump, get_labels, centers_dense
from ..utils import load, merge_logs


def rechunk(X: np.array, *, chunk_size: int) -> list[np.array]:
    """Chunk a NumPy array into arrays of a given maximum size.

    Parameters
    ----------
    X: np.array
        Array to rechunk.
    chunk_size: int
        Maximum size for an array chunk in byte.

    Returns
    -------
    list[np.array]
        Newly created chunks from original array.
    """
    n_chunks = math.ceil(X.itemsize * X.size / chunk_size)
    return np.array_split(X, n_chunks)


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

    if scheduler.lower() == "slurm":
        scheduler = os.environ["MASTER_URL"]

    conf = SparkConf().setMaster(scheduler).setAppName(experiment)
    sc = SparkContext.getOrCreate(conf=conf)

    start_time = time.time()
    common_args = {
        "benchmark_folder": benchmark_folder,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    files = glob.glob(input_folder + "/*.nii")
    paths = sc.parallelize(files, len(files))
    blocks = paths.map(lambda p: load(p, **common_args))
    voxels = blocks.flatMap(
        lambda block: rechunk(block[1].flatten(), chunk_size=6.4e7)
    )  # 64MB chunks

    n_clusters = 3
    centroids = np.linspace(
        voxels.map(np.min).min(),
        voxels.map(np.max).max(),
        num=n_clusters,
    )
    print(centroids)

    for _ in range(iterations):  # Disregard convergence.

        labels = voxels.map(lambda X: get_labels(X, centroids, **common_args))

        r = voxels.zip(labels).map(
            lambda x: centers_dense(x[0], x[1], n_clusters, **common_args)
        )
        centers_meta = np.array(r.collect()).sum(axis=0)
        new_centers = centers_meta[:, 0]
        counts = centers_meta[:, 1]
        counts = np.maximum(counts, 1, out=counts)
        centroids = new_centers / counts

        print(f"{centroids=}")

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
