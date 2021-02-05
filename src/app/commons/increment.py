import os
from time import time, sleep

import nibabel as nib

from ..utils import log


def increment(
    data, delay, increment_data=1, *, benchmark, start, output_folder, experiment
):
    """Increment the data of a Nifti image by 1.

    :param filename: str -- representation of the path for the input file.
    :param data: nifti1Image -- image to manipulate.
    :param metadata: tuple -- of the form (image affine, image header).
    :param delay: int -- sleep time for the task
    :return: tuple -- of the form (filename, data, (image affine,
    image header), iteration+1).
    """
    start_time = time() - start

    filename = data[0]
    content = data[1]
    metadata = data[2]
    del data

    filename_log = filename
    if not isinstance(increment_data, int):
        filename_log = f"{filename}:{increment_data[0]}"
        increment_data = increment_data[1]

    content += increment_data
    sleep(delay)

    end_time = time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            filename_log,
            output_folder,
            experiment,
            increment.__name__,
        )

    return filename, content, metadata


def dump(data, *, benchmark, start, output_folder, experiment):
    """Save a Nifti image.

    Parameters
    ----------
    data: (str, np.array, (np.array, np.array))
        Filename, image, and image header and affine.

    Returns
    -------
    f_out : str
        Output path where the image is saved.
    "SUCCESS" : str
        Indicates that the pipeline succeeded.
    """
    start_time = time() - start

    filename = data[0]
    content = data[1]
    metadata = data[2]

    bn = os.path.basename(filename[:-3] + "nii")  # Save in nifti format
    f_out = os.path.join(output_folder, bn)

    img = nib.Nifti1Image(content, metadata[0], header=metadata[1])
    nib.save(img, f_out)

    end_time = time() - start

    if benchmark:
        log(
            start_time,
            end_time,
            filename,
            output_folder,
            experiment,
            dump.__name__,
        )

    return f_out, "SUCCESS"
