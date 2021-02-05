import glob
import os
import time

import dask
import dask.array as da
from dask.distributed import Client
from dask_jobqueue import SLURMCluster

import numpy as np

from ..commons.kmeans import classify_block, dump
from ..utils import load, log, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_worker: int,
    benchmark: bool,
    *,
    iterations,
) -> None:
    experiment = f"dask:kmeans:iterations={iterations}"
    start_time = time.time()
    common_args = {
        "benchmark": benchmark,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    SLURM = scheduler.lower() == "slurm"
    if SLURM:
        hostname = os.environ["HOSTNAME"]
        cluster = SLURMCluster(scheduler_options={"host": hostname})
        client = Client(cluster)
        cluster.scale(n_worker)
    else:
        client = Client(scheduler)

    blocks = [
        dask.delayed(load)(
            filename,
            **common_args,
        ).persist()
        for filename in glob.glob(input_folder + "/*.nii")
    ]

    sample = blocks[0].compute()[1]  # Compute a sample block to obtain dtype and shape.

    voxels = (
        da.stack(
            [
                da.from_delayed(block[1], dtype=sample.dtype, shape=sample.shape)
                for block in blocks
            ]
        )
        .reshape(-1)
        .rechunk(16_000_000)  # 128MB chunks
        .persist()
    )
    del sample

    # Pick random initial centroids
    centroids = np.linspace(
        *dask.compute(da.min(voxels), da.max(voxels)),
        num=3,
    )

    centroid_index = None
    for _ in range(0, iterations):  # Disregard convergence.
        start = time.time() - start_time

        centroid_index = da.argmin(
            da.fabs(da.subtract.outer(voxels, centroids)), axis=1
        ).persist()

        centroids = np.array(
            [
                da.mean(voxels[centroid_index == c], dtype=np.float32).persist()
                for c in range(len(centroids))
            ],
            dtype=np.uint16,
        )
        print(f"{centroids=}")

        end_time = time.time() - start_time

        if benchmark:
            log(
                start,
                end_time,
                "all",
                output_folder,
                experiment,
                "update_centroids",
            )

    del voxels
    del centroid_index

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

    if benchmark:
        merge_logs(
            output_folder=output_folder,
            experiment=experiment,
        )
