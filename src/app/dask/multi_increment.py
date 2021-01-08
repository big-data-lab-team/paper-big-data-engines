import glob
import os
import random
import time

import dask
from dask.distributed import Client

from ..commons.increment import increment, dump
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    benchmark: bool,
    *,
    iterations: int,
    delay: int,
    seed: int = 1234,
) -> None:
    experiment = (
        f"dask:multi-increment:iterations={iterations}:delay={delay}:seed{seed}"
    )
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

    results = []
    random.seed(seed)
    for block in blocks:
        for _ in range(iterations):
            block = dask.delayed(increment)(
                block,
                delay=delay,
                increment_data=random.choice(blocks)[1],
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
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )
