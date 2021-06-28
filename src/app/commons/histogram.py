import os
from time import time

import numpy as np

from ..utils import log


def flatten(arr, *, benchmark_folder, start, experiment, filename, **kwargs):
    start_time = time() - start

    arr = arr.flatten()

    end_time = time() - start

    if benchmark_folder:
        log(
            start_time, end_time, filename, benchmark_folder, experiment, "flatten",
        )
    return filename, arr


def calculate_histogram(
    arr, *, benchmark_folder, start, experiment, filename, **kwargs
):
    start_time = time() - start

    histogram = np.histogram(arr, bins=range(2 ** 16))[0]

    end_time = time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            filename,
            benchmark_folder,
            experiment,
            "calculate_histogram",
        )
    return histogram


def combine_histogram(x, y, *, benchmark_folder, start, experiment, **kwargs):
    start_time = time() - start

    rv = x + y

    end_time = time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            "all_file",
            benchmark_folder,
            experiment,
            "combine_histogram",
        )
    return rv


def save_histogram(
    histogram, *, benchmark_folder, start, output_folder, experiment, **kwargs
):
    start_time = time() - start

    with open(os.path.join(output_folder, "histogram.csv"), "w") as f_out:
        for i, elm in enumerate(histogram):
            f_out.write(f"{i};{elm}\n")

    end_time = time() - start

    if benchmark_folder:
        log(
            start_time,
            end_time,
            "all_file",
            benchmark_folder,
            experiment,
            "save_histogram",
        )
