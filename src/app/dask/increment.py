import glob
import os
import time
import uuid

import dask
from dask.distributed import Client
from dask_jobqueue import SLURMCluster

from ..commons.increment import increment, dump
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_worker: int,
    benchmark_folder: str,
    *,
    block_size: int,
    iterations: int,
    delay: int,
) -> None:
    experiment = os.path.join(
        f"dask:increment:{n_worker=}:{block_size=}:{iterations=}:{delay=}",
        str(uuid.uuid1()),
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

    results = []
    for block in blocks:
        for _ in range(iterations):
            block = dask.delayed(increment)(
                block,
                delay=delay,
                **common_args,
            )

        results.append(
            dask.delayed(dump)(
                block,
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
