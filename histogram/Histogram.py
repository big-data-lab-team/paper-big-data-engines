from collections import defaultdict
from time import time

from utils import benchmark


def calculate_histogram(arr, *, args, start, filename):
    start_time = time() - start

    arr = arr.flatten('F')

    histogram = defaultdict(int)
    for x in arr:
        histogram[x] += 1

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

    rv = {k: x.get(k, 0) + y.get(k, 0) for k in set(x) | set(y)}

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
