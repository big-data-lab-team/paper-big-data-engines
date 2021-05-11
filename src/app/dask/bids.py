import os
import time

import dask
from dask.distributed import Client
from dask_jobqueue import SLURMCluster

from ..commons.bids import run_group, run_participant, site_crawler, subject_crawler
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    n_worker: int,
    benchmark_folder: str,
    container_path: str,
) -> None:
    experiment = f"dask:bids:{n_worker=}"
    start_time = time.time()
    common_args = {
        "benchmark_folder": benchmark_folder,
        "start": start_time,
        "input_folder": input_folder,
        "output_folder": output_folder,
        "experiment": experiment,
        "container_path": container_path,
    }

    SLURM = scheduler.lower() == "slurm"
    if SLURM:
        hostname = os.environ["HOSTNAME"]
        cluster = SLURMCluster(scheduler_options={"host": hostname})
        client = Client(cluster)
        cluster.scale(jobs=n_worker)

    else:
        client = Client(scheduler)

    subjects = subject_crawler(input_folder)
    sites = site_crawler(input_folder)

    for site in sites:
        site_folder = os.path.join(output_folder, site)
        if not os.path.exists(site_folder):
            os.mkdir(site_folder)

    futures = client.compute(
        [
            dask.delayed(run_participant)(
                subject_id=subject[1], site=subject[0], **common_args
            )
            for subject in subjects
        ]
    )
    client.gather(futures)
    futures = client.compute(
        [dask.delayed(run_group)(site=site, **common_args) for site in sites]
    )
    client.gather(futures)

    client.close()
    if SLURM:
        cluster.scale(0)

    if benchmark_folder:
        merge_logs(
            benchmark_folder=benchmark_folder,
            experiment=experiment,
        )
