from glob import glob
import subprocess
from time import time

from utils import benchmark


def subject_crawler(path):
    return [
        (site_dir, subj_id.split("/")[-2].split("-")[-1])
        for site_dir in glob(f"{path}")
        for subj_id in glob(f"{site_dir}/*/")
    ]


def run_participant(*, subject_id, start, args):
    start_time = time() - start

    subprocess.run(
        [
            "singularity",
            "exec",
            "-B",
            "/nfs/singularity-image:/run,/nfs:/nfs",
            "/nfs/singularity-image/bids_example.simg",
            "bash",
            "/run/participant.sh",
            args.bids_dir,
            args.output_dir,
            subject_id,
        ],
        shell=True,
    )

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            subject_id,
            args.output_dir,
            args.experiment,
            run_participant.__name__,
        )


def run_group(*, start, args):
    start_time = time() - start

    subprocess.run(
        [
            "singularity",
            "exec",
            "-B",
            "/nfs/singularity-image:/run,/nfs:/nfs",
            "/nfs/singularity-image/bids_example.simg",
            "bash",
            "/run/group.sh",
            args.bids_dir,
            args.output_dir,
        ],
        shell=True,
    )

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            "all_file",
            args.output_dir,
            args.experiment,
            run_group.__name__,
        )
