import glob
import os
import time
import uuid

import dask
import dask.array as da
from dask.distributed import Client
from dask_jobqueue import SLURMCluster
import numba
import numpy as np

from ..commons.kmeans import classify_block, dump
from ..utils import load, log, merge_logs


@numba.njit(nogil=True, fastmath=True)
def _centers_dense(X, labels, n_clusters):
    centers = np.zeros(n_clusters, dtype=np.uint16)

    for i in range(X.shape[0]):
        centers[labels[i]] += X[i]

    return centers


def get_labels(X, centroids):
    array = np.subtract.outer(X, centroids)
    np.square(array, out=array)
    return np.argmin(array, axis=1)


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
        f"dask:kmeans:{n_worker=}:{block_size=}:{iterations=}", str(uuid.uuid1())
    )

    SLURM = scheduler.lower() == "slurm"
    if SLURM:
        hostname = os.environ["HOSTNAME"]
        cluster = SLURMCluster(scheduler_options={"host": hostname})
        client = Client(cluster)
        cluster.scale(jobs=n_worker)
    else:
        client = Client(scheduler)

    start_time = time.time()
    common_args = {
        "benchmark_folder": benchmark_folder,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    blocks = [
        dask.delayed(load)(
            filename,
            **common_args,
        )
        for filename in glob.glob(input_folder + "/*.nii")
    ]

    sample = blocks[0].compute()[1]  # Compute a sample block to obtain dtype and shape.
    dtype = sample.dtype

    voxels = (
        da.stack(
            [
                da.from_delayed(block[1], dtype=dtype, shape=sample.shape)
                for block in blocks
            ],
        )
        .reshape(-1)
        .rechunk(block_size_limit=128 * 1024 ** 2)  # 128MB chunks
    )
    del sample

    n_clusters = 3
    centroids = np.linspace(
        da.min(voxels).compute(),
        da.max(voxels).compute(),
        num=n_clusters,
    )

    labels = None
    for _ in range(iterations):  # Disregard convergence.
        start = time.time() - start_time

        labels = da.map_blocks(
            lambda X: get_labels(X, centroids),
            voxels,
            dtype=dtype,
        )

        # Ref: from dask_ml.cluster.k_means::_kmeans_single_lloyd
        r = da.blockwise(
            _centers_dense,
            "i",
            voxels,
            "i",
            labels,
            "i",
            n_clusters,
            None,
            dtype=voxels.dtype,
        )
        new_centers = da.from_delayed(sum(r.to_delayed()), (n_clusters,), voxels.dtype)
        counts = da.bincount(labels, minlength=n_clusters)
        # Require at least one per bucket, to avoid division by 0.
        counts = da.maximum(counts, 1)
        new_centers = new_centers / counts
        (centroids,) = dask.compute(new_centers)

        print(f"{centroids=}")
        del labels

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

    del voxels
    del labels

    results = []
    for block in blocks:
        results.append(
            dask.delayed(dump)(
                dask.delayed(classify_block)(block, centroids, **common_args),
                **common_args,
            )
        )

    futures = client.compute(results)
    client.gather(futures)

    client.close()
    if SLURM:
        cluster.scale(0)

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
