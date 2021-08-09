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

from ..commons.kmeans import classify_block, dump, get_labels, _centers_dense
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
        .rechunk(block_size_limit=64 * 1024 ** 2)  # 64MB chunks
    )

    n_clusters = 3
    centroids = np.linspace(
        da.min(voxels).compute(),
        da.max(voxels).compute(),
        num=n_clusters,
    )
    print(f"{centroids=}")

    labels = None
    for _ in range(iterations):  # Disregard convergence.

        labels = da.map_blocks(
            lambda X: get_labels(X, centroids, **common_args),
            voxels,
            dtype=np.ubyte,
        )

        # Ref: from dask_ml.cluster.k_means::_kmeans_single_lloyd
        r = da.blockwise(
            _centers_dense,
            "ik",
            voxels,
            "i",
            labels,
            "i",
            n_clusters,
            None,
            **common_args,
            new_axes={"k": 2},
            dtype=voxels.dtype,
        )
        centers_meta = np.sum(dask.compute(*r.to_delayed().flatten()), axis=0)
        new_centers = centers_meta[:, 0]
        counts = centers_meta[:, 1]
        counts = np.maximum(counts, 1, out=counts)
        centroids = new_centers / counts

        print(f"{centroids=}")

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
