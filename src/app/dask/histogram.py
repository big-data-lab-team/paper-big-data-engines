from functools import reduce
import glob
import time

import dask
from dask.distributed import Client
from dask_jobqueue import SLURMCluster

from ..commons.histogram import (
    calculate_histogram,
    combine_histogram,
    flatten,
    save_histogram,
)
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_worker: int,
    benchmark: bool,
) -> None:
    experiment = f"dask:histogram"
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
        cluster.scale(n_worker)
    else:
        client = Client(scheduler)

    print(client)

    blocks = [
        dask.delayed(load)(
            filename,
            **common_args,
        )
        for filename in glob.glob(input_folder + "/*.nii")
    ]

    partial_histogram = []
    for block in blocks:
        img = dask.delayed(flatten)(
            block[1],
            **common_args,
            filename=block[0],
        )

        partial_histogram.append(
            dask.delayed(calculate_histogram)(
                img[1],
                **common_args,
                filename=img[0],
            )
        )

    histogram = dask.delayed(reduce)(
        lambda x, y: combine_histogram(
            x,
            y,
            **common_args,
        ),
        partial_histogram,
    )

    future = client.compute(histogram)
    histogram = client.gather(future)

    save_histogram(
        histogram,
        **common_args,
    )

    client.close()
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )
