import sys

sys.path.append("/nfs/SOEN-499-Project")

from time import time, sleep

from utils import benchmark


def increment(img_rdd, delay, start, args):
    """Increment the data of a Nifti image by 1.

    :param filename: str -- representation of the path for the input file.
    :param data: nifti1Image -- image to manipulate.
    :param metadata: tuple -- of the form (image affine, image header).
    :param delay: int -- sleep time for the task
    :return: tuple -- of the form (filename, data, (image affine,
    image header), iteration+1).
    """
    start_time = time() - start

    filename = img_rdd[0]
    data = img_rdd[1]
    metadata = img_rdd[2]

    data += 1
    sleep(delay)

    end_time = time() - start

    if args.benchmark:
        benchmark(
            start_time,
            end_time,
            filename,
            args.output_dir,
            args.experiment,
            increment.__name__,
        )

    return filename, data, metadata
