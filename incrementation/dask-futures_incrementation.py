import argparse
from time import time
import os

from dask.distributed import Client, fire_and_forget

from Increment import increment, save_results
from utils import crawl_dir, read_img


if __name__ == "__main__":

    start = time()  # Start time of the pipeline

    parser = argparse.ArgumentParser(description="BigBrain incrementation")
    parser.add_argument("scheduler", type=str, help="Scheduler ip and port")
    parser.add_argument(
        "bb_dir",
        type=str,
        help=("The folder containing BigBrain NIfTI images" "(local fs only)"),
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help=("the folder to save incremented images to" "(local fs only)"),
    )
    parser.add_argument(
        "experiment", type=str, help="Name of the experiment being performed"
    )
    parser.add_argument("iterations", type=int, help="number of iterations")
    parser.add_argument(
        "delay", type=float, help="sleep delay during " "incrementation"
    )
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    client.upload_file("/nfs/paper-big-data-engines/utils.py")  # Allow workers to use module
    client.upload_file("/nfs/paper-big-data-engines/incrementation/Increment.py")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    client.scatter(paths)

    results = []
    for path in paths:
        img = client.submit(read_img, path, start=start, args=args)

        # Increment the data n time:
        for _ in range(args.iterations):
            img = client.submit(
                increment, img, delay=args.delay, start=start, args=args
            )

        # Save the data
        results.append(client.submit(save_results, img, start=start, args=args))

        # Execute the tasks
        fire_and_forget(img)

    client.gather(results)

    client.close()
