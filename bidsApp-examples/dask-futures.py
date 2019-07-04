import argparse
import sys
from time import time

import dask
from dask.distributed import Client, fire_and_forget

sys.path.append("/nfs/paper-big-data-engines")


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

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    client.upload_file("/nfs/paper-big-data-engines/bidsApp-examples/Example.py")
    from Example import run_group, run_participant, subject_crawler

    # Retrieve all subject path
    subjects = subject_crawler(args.bids_dir)
    client.scatter(subjects)

    results = list()
    for subject in subjects:
        results.append(
            client.submit(
                run_participant, subject_id=subject[1], start=start, args=args
            )
        )

    client.gather(results)

    run_group(start=start, args=args)