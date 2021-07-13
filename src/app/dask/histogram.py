import glob
import os
import time
import uuid

import dask.bag as db
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
    benchmark_folder: str,
    *,
    block_size: int,
) -> None:
    experiment = os.path.join(
        f"dask:histogram:{n_worker=}:{block_size=}", str(uuid.uuid1())
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

    filenames = glob.glob(input_folder + "/*.nii")
    paths = db.from_sequence(filenames, npartitions=len(filenames))
    img = paths.map(lambda p: load(p, **common_args))

    img = img.map(lambda x: flatten(x[1], **common_args, filename=x[0]))

    partial_histogram = img.map(
        lambda x: calculate_histogram(x[1], **common_args, filename=x[0])
    )

    histogram = partial_histogram.fold(
        lambda x, y: combine_histogram(x, y, **common_args),
    ).compute()

    save_histogram(
        histogram,
        **common_args,
    )

    client.close()
    if SLURM:
        cluster.scale(0)

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
