from collections import defaultdict
from time import time

import numpy as np

from utils import benchmark


def flatten(arr, *, args, start, filename):
    start_time = time() - start

    arr = arr.flatten("F")

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            "flatten",
        )
    return filename, arr


def calculate_histogram(arr, *, args, start, filename):
    start_time = time() - start

    histogram = np.histogram(arr, bins=range(2**16))[0]

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            "calculate_histogram",
        )
    return histogram


def combine_histogram(x, y, *, args, start):
    start_time = time() - start

    rv = x + y

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            "all_file",
            args.output_dir,
            args.experiment,
            "combine_histogram",
        )
    return rv


def save_histogram(histogram, *, args, start):
    start_time = time() - start

    with open(f"{args.output_dir}/histogram.csv", "w") as f_out:
        for i, elm in enumerate(histogram):
            f_out.write(f"{i};{elm}\n")

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            "all_file",
            args.output_dir,
            args.experiment,
            "save_histogram",
        )