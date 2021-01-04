import glob
import os
import pathlib
import time

import dask
from dask.distributed import Client

from ..commons.increment import increment, dump
from ..utils import load


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    benchmark: bool,
    *,
    iterations: int,
    delay: int,
) -> None:
    experiment = f"dask:increment:{iterations=}:{delay=}"
    start_time = time.time()

    client = Client(scheduler)

    blocks = [
        dask.delayed(load)(
            filename,
            benchmark=benchmark,
            start=start_time,
            output_folder=output_folder,
            experiment=experiment,
        )
        for filename in glob.glob(input_folder + "/*.nii")
    ]

    results = []
    for block in blocks:
        for _ in range(iterations):
            block = dask.delayed(increment)(
                block,
                delay=delay,
                benchmark=benchmark,
                start=start_time,
                output_folder=output_folder,
                experiment=experiment,
            )

        results.append(
            dask.delayed(dump)(
                block,
                benchmark=benchmark,
                start=start_time,
                output_folder=output_folder,
                experiment=experiment,
            )
        )

    futures = client.compute(results)
    client.gather(futures)

    client.close()
