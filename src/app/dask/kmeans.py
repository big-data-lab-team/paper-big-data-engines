import glob
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
    n_workers: int,
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

    if scheduler.lower() == "slurm":
        cluster = SLURMCluster()
        client = Client(cluster)
        cluster.scale(n_workers)
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
        da.min(voxels).compute(),
        da.max(voxels).compute(),
        num=3,
    )

    centroid_index = None
    for _ in range(0, iterations):  # Disregard convergence.
        start = time.time() - start_time

        centroid_index = da.argmin(
            da.fabs(da.subtract.outer(voxels, centroids)), axis=1
        ).persist()

        centroids = np.array(
            [da.mean(voxels[centroid_index == c]).persist() for c in range(len(centroids))]
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
        block = dask.delayed(classify_block)(block, centroids, **common_args)
        results.append(
            dask.delayed(dump)(
                block,
                **common_args,
            )
        )

    dask.compute(*results)

    client.close()
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )
