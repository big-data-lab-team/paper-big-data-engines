from glob import glob
import subprocess
from time import time

from utils import benchmark


def subject_crawler(path):
    return [
        (site_dir, subj_dir.split("/")[-2].split("-")[-1])
        for site_dir in glob(f"{path}")
        for subj_dir in glob(f"{site_dir}/*/")
    ]


def run_participant(*, subject_dir, start, args, input_dir, output_dir):
    start_time = time() - start

    path = "../"
    subprocess.run(
        [
            f"{path}/bids_example.img",
            input_dir,
            output_dir,
            "participant",
            "--participant_label",
            subject_dir,
        ],
        shell=True,
    )

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            subject_dir,
            args.output_dir,
            args.experiment,
            run_participant.__name__,
        )


def run_group(*, start, args, file_, output_dir):
    start_time = time() - start

    path = "../"
    subprocess.run(
        [f"{path}/bids_example.img", "/nfs/bids-data/RawDataBIDS", output_dir, "group"],
        shell=True,
    )

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            file_,
            args.output_dir,
            args.experiment,
            run_group.__name__,
        )
