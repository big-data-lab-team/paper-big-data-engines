import glob
import time

import dask
import dask.array as da
import dask.bag as db
from dask.distributed import Client
import nibabel as nib
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
    experiment = f"dask:kmeans:iterations={iterations}"
    start_time = time.time()
    common_args = {
        "benchmark": benchmark,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    client = Client(scheduler)

    blocks = [
        dask.delayed(load)(
            filename,
            **common_args,
        )
        for filename in glob.glob(input_folder + "/*.nii")
    ]

    sample = blocks[0].compute()[1]  # Compute a sample block to obtain dtype and shape.
    voxels = (
        da.concatenate(
            [
                da.from_delayed(block[1], dtype=sample.dtype, shape=sample.shape)
                for block in blocks
            ]
        )
        .reshape(-1)
        .rechunk(16_000_000, balance=True)
    )

    # Pick random initial centroids
    # TODO benchmark
    centroids = da.random.choice(
        da.unique(voxels).compute(), size=3, replace=False
    ).compute()

    for _ in range(0, iterations):  # Disregard convergence.
        start = time.time() - start_time

        centroid_index = voxels.map_blocks(
            lambda block: closest_centroids(block, centroids)
        )

        # Find centroid (total, count) => total/count = centroid
        centroids = np.array(
            [da.mean(voxels[centroid_index == i]) for i in range(len(centroids))]
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

    results = []
    for block in blocks:
        block = dask.delayed(classify_block)(block, centroids)
        results.append(
            dask.delayed(dump)(
                block,
                **common_args,
            )
        )

    futures = client.compute(results)
    client.gather(futures)

    client.close()
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )
