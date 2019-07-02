import argparse
import sys
from time import time


from pyspark import SparkConf, SparkContext

from Example import run_group, run_participant, subject_crawler

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
    conf = SparkConf().setAppName("Spark Incrementation")
    sc = SparkContext.getOrCreate(conf=conf)
    print("Connected")

    # Retrieve all subject path
    subjects_to_analyze = sc.parallelize(subject_crawler(args.bids_dir))

    subjects_to_analyze.map(
        lambda x: run_participant(
            subject_dir=x[1],
            start=start,
            args=args,
            input_dir=x[0],
            output_dir=args.output_dir,
        )
    )

    run_group(start=start, args=args, output_dir=args.output_dir)
