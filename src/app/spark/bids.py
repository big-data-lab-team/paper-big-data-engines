import glob
import os
import time

from pyspark import SparkConf, SparkContext

from ..commons.bids import run_group, run_participant, site_crawler, subject_crawler
from ..utils import load, merge_logs


def run(
    input_folder: str,
    output_folder: str,
    scheduler: str,
    benchmark: bool,
    container_path: str,
) -> None:
    experiment = f"spark:bids"
    start_time = time.time()
    common_args = {
        "benchmark": benchmark,
        "start": start_time,
        "input_folder": input_folder,
        "output_folder": output_folder,
        "experiment": experiment,
        "container_path": container_path,
    }

    conf = SparkConf().setMaster(scheduler).setAppName(experiment)
    sc = SparkContext.getOrCreate(conf=conf)

    subjects_to_analyze = sc.parallelize(subject_crawler(input_folder), 512)

    subjects_to_analyze.map(
        lambda x: run_participant(subject_id=x[1], site=x[0], **common_args)
    ).collect()

    sites = sc.parallelize(site_crawler(input_folder), 512)
    sites.map(lambda x: run_group(site=x, **common_args)).collect()
    merge_logs(
        output_folder=output_folder,
        experiment=experiment,
    )