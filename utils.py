from io import BytesIO
import os
import socket
import uuid
from time import time
import threading

import nibabel as nib
import numpy as np


def benchmark(start, end, filename, output_dir, experiment, func_name):
    """Records function lifetime to a file.

    Parameters
    ----------
    start : float
        Start time of the function.
    end : float
        End time of the function.
    filename : str
        Name of the filename processed.
    output_dir : str
        Directory were the output is saved.
    experiment : str
        Tag for the experiment.
    func_name : str
        Name of the function benchmarked.
    """
    benchmark_dir = os.path.join(output_dir, "benchmarks/" + experiment)
    os.makedirs(benchmark_dir, exist_ok=True)

    benchmark_file = os.path.join(
        benchmark_dir, "benchmark-{}-{}.txt".format(experiment, uuid.uuid1())
    )

    bn = os.path.basename(filename)
    node = socket.gethostname()
    thread = threading.currentThread().ident
    pid = os.getpid()

    with open(benchmark_file, "a+") as f_out:
        # Write
        f_out.write(
            "{0},{1},{2},{3},{4},{5},{6}\n".format(
                func_name, start, end, bn, node, thread, pid
            )
        )


def crawl_dir(input_dir):
    """Crawl the input directory to retrieve MINC files.

    Parameters
    ----------
    input_dir: str
        Representation of the path for the input file.

    Returns
    -------
    rv : list
        List of the retrieved path.
    """
    rv = list()
    for folder, subs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith(".nii"):
                path = os.path.join(folder, filename)
                rv.append(path)
    return rv


def read_img(filename, start, args):
    """Read a Nifti image as a byte stream.

    Parameters
    ----------
    filename: str
        Representation of the path for the input file.

    Returns
    -------
    filename : str
        Representation of the path for the input file.
    data : np.array
        Data of the nifti imaeg read.
    (img.affine, img.header) : (np.array, np.array)
        Affine and header of the nifti image read.
    """
    start_time = time() - start

    img = None
    with open(filename, "rb") as f_in:
        fh = nib.FileHolder(fileobj=BytesIO(f_in.read()))
        img = nib.Nifti1Image.from_file_map({"header": fh, "image": fh})
    data = np.asanyarray(img.dataobj)

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            read_img.__name__,
        )

    return filename, data, (img.affine, img.header)
