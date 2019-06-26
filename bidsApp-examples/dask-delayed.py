import argparse
from glob import glob
import os
import subprocess
import sys
from time import time

import dask
from dask.distributed import Client
import nibabel
import numpy

sys.path.append("/nfs/paper-big-data-engines")


def run(command, *, start, args):

    start_time = time() - start

    subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            brain_file,
            args.output_dir,
            args.experiment,
            run.__name__,
        )


def get_data(brain_file, *, start, args):

    start_time = time() - start

    data = nibabel.load(brain_file).get_data()

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            brain_file,
            args.output_dir,
            args.experiment,
            get_data.__name__,
        )
    return data


if __name__ == "__main__":
    start = time()

    parser = argparse.ArgumentParser(description="Example BIDS App entrypoint script.")
    parser.add_argument("scheduler", type=str, help="Scheduler ip and port")
    parser.add_argument(
        "bids_dir",
        help="The directory with the input dataset "
        "formatted according to the BIDS standard.",
    )
    parser.add_argument(
        "output_dir",
        help="The directory where the output files "
        "should be stored. If you are running group level analysis "
        "this folder should be prepopulated with the results of the"
        "participant level analysis.",
    )
    parser.add_argument(
        "experiment", type=str, help="Name of the experiment being performed"
    )
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    client.upload_file("/nfs/paper-big-data-engines/utils.py")
    from utils import benchmark

    # running participant level
    # find all T1s and skullstrip them
    for subject_label in subjects_to_analyze:
        for T1_file in glob(
            os.path.join(args.bids_dir, "sub-%s" % subject_label, "anat", "*_T1w.nii*")
        ) + glob(
            os.path.join(
                args.bids_dir, "sub-%s" % subject_label, "ses-*", "anat", "*_T1w.nii*"
            )
        ):
            out_file = os.path.split(T1_file)[-1].replace("_T1w.", "_brain.")
            cmd = "bet %s %s" % (T1_file, os.path.join(args.output_dir, out_file))
            print(cmd)
            # dask.delayed(run)(cmd, start=start, args=args)

    # running group level
    brain_sizes = []
    for subject_label in subjects_to_analyze:
        for brain_file in glob(
            os.path.join(args.output_dir, "sub-%s*.nii*" % subject_label)
        ):
            data = dask.delayed(get_data)(brain_file, start=start, args=args)
            # calcualte average mask size in voxels
            brain_sizes.append((data != 0).sum())

    with open(os.path.join(args.output_dir, "avg_brain_size.txt"), "w") as fp:
        fp.write("Average brain size is %g voxels" % numpy.array(brain_sizes).mean())
