from glob import glob
import os
import subprocess
from time import time

from ..utils import log


def subject_crawler(path):
    return [
        (site_dir.split("/")[-2], subj_id.split("/")[-2].split("-")[-1])
        for site_dir in glob(f"{path}/*/")
        for subj_id in glob(f"{site_dir}/sub-*/")
    ]


def site_crawler(path):
    return [(site_dir.split("/")[-2]) for site_dir in glob(f"{path}/*/")]


def run_participant(
    subject_id,
    site,
    *,
    benchmark_folder,
    start,
    input_folder,
    output_folder,
    experiment,
    container_path,
    **kwargs,
):
    start_time = time() - start

    subprocess.run(
        " ".join(
            [
                container_path,
                os.path.join(input_folder, site),
                os.path.join(output_folder, site),
                "participant",
                "--skip_bids_validator",
                "--participant_label",
                subject_id,
            ]
        ),
        shell=True,
    )

    end_time = time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            subject_id,
            benchmark_folder,
            experiment,
            run_participant.__name__,
        )


def run_group(
    site,
    *,
    benchmark_folder,
    start,
    input_folder,
    output_folder,
    experiment,
    container_path,
    **kwargs,
):
    start_time = time() - start

    subprocess.run(
        " ".join(
            [
                container_path,
                os.path.join(input_folder, site),
                os.path.join(output_folder, site),
                "group",
                "--skip_bids_validator",
            ]
        ),
        shell=True,
    )

    end_time = time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            "all_file",
            benchmark_folder,
            experiment,
            run_group.__name__,
        )
