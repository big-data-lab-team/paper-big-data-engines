import argparse
import os
from time import time

import dask.bag as db
from dask.distributed import Client, LocalCluster

from Kmeans import add_component_wise, closest_centroid, get_voxels, save_results
from utils import benchmark, crawl_dir, read_img


if __name__ == "__main__":

    start = time()  # Start time of the pipeline

    parser = argparse.ArgumentParser(description="BigBrain Kmeans")
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
    parser.add_argument("--benchmark", action="store_true", help="benchmark results")

    args = parser.parse_args()

    # Cluster scheduler
    cluster = args.scheduler
    client = Client(cluster)

    print(client)
    client.upload_file("/nfs/SOEN-499-Project/utils.py")  # Allow workers to use module
    client.upload_file("/nfs/SOEN-499-Project/kmeans/Kmeans.py")

    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = db.from_sequence(paths, npartitions=len(paths))
    img_rdd = paths.map(lambda p: read_img(p, start=start, args=args)).persist()

    voxels = img_rdd.map(lambda x: get_voxels(x[1])).flatten()

    centroids = [0.0, 125.8, 251.6, 377.4]  # Initial centroids
    voxel_pair = None
    frequency_pair = voxels.frequencies().persist()

    for i in range(0, args.iterations):  # Disregard convergence.
        start_time = time() - start

        voxel_pair = frequency_pair.map(
            lambda x: (closest_centroid(x, centroids))
        )

        # Reduce voxel assigned to the same centroid together
        classe_pairs = (
            voxel_pair.map(lambda x: (x[0], (x[1][0] * x[1][1], x[1][1])))
            .foldby(0, add_component_wise, (0, (0, 0)))
            .map(lambda x: x[1][1])
            .compute()
        )
        # Find centroid (total, count) => total/count = centroid
        centroids = [pair[0] / pair[1] for pair in classe_pairs]

        end_time = time() - start

        if args.benchmark:
            benchmark(
                start_time,
                end_time,
                "all_file",
                args.output_dir,
                args.experiment,
                "update_centroids",
            )

    voxel_pair = voxel_pair.compute()
    img_rdd.map(lambda x: save_results(x, voxel_pair, start=start, args=args)).compute()
