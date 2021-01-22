import glob
import os
import time

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
    benchmark: bool,
    *,
    iterations: int,
    delay: int,
) -> None:
    experiment = f"dask:increment:iterations={iterations}:delay={delay}"
    start_time = time.time()
    common_args = {
        "benchmark": benchmark,
        "start": start_time,
        "output_folder": output_folder,
        "experiment": experiment,
    }

    if scheduler.lower() == "slurm":
        hostname = os.environ["HOSTNAME"]
        cluster = SLURMCluster(scheduler_options={"host": hostname})
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
    if benchmark:
        merge_logs(
            output_folder=output_folder,
            experiment=experiment,
        )
