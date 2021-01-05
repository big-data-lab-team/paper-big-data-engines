from collections import defaultdict
import os
from time import time

import numpy as np

from ..utils import log


def flatten(arr, *, benchmark, start, output_folder, experiment, filename):
    start_time = time() - start

    arr = arr.flatten("F")

    end_time = time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            filename,
            output_folder,
            experiment,
            "flatten",
        )
    return filename, arr


def calculate_histogram(arr, *, benchmark, start, output_folder, experiment, filename):
    start_time = time() - start

    histogram = np.histogram(arr, bins=range(2 ** 16))[0]

    end_time = time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            filename,
            output_folder,
            experiment,
            "calculate_histogram",
        )
    return histogram


def combine_histogram(x, y, *, benchmark, start, output_folder, experiment):
    start_time = time() - start

    rv = x + y

    end_time = time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            "all_file",
            output_folder,
            experiment,
            "combine_histogram",
        )
    return rv


def save_histogram(histogram, *, benchmark, start, output_folder, experiment):
    start_time = time() - start

    with open(
        os.path.join(output_folder, "benchmarks", experiment, "histogram.csv"), "w"
    ) as f_out:
        for i, elm in enumerate(histogram):
            f_out.write(f"{i};{elm}\n")

    end_time = time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            "all_file",
            output_folder,
            experiment,
            "save_histogram",
        )