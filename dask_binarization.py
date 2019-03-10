import argparse
import os
from io import BytesIO
import numpy as np
import nibabel as nib
import dask.bag as db
from utils import benchmark


def retrieve_input(input_dir):
    """
    
    :param input_dir:
    :return:
    """
    rv = list()
    for folder, subs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.mnc'):
                path = os.path.join(folder, filename)
                with open(path, 'rb') as f:
                    rv.append((path, f.read()))
    return rv


def read_img(filename, is_benchmarking, output_dir, *, data=None):
    """
    
    :param filename:
    :param is_benchmarking:
    :param output_dir:
    :param data:
    :return:
    """
    fh = nib.FileHolder(fileobj=BytesIO(data))
    img = nib.Nifti1Image.from_file_map({'header': fh, 'image': fh})
    
    data = img.get_data()
    
    return (filename, data, (img.affine, img.header))


def binarize_data(filename, is_benchmarking, output_dir, *, data=None,
                  metadata=None):
    """
    
    :param filename:
    :param is_benchmarking:
    :param output_dir:
    :param data:
    :param metadata:
    :return:
    """
    pass
    return (filename, data, metadata)


def save_binarization(filename, is_benchmarking, output_dir, *, data=None,
                      metadata=None):
    """
    
    :param filename:
    :param is_benchmarking:
    :param output_dir:
    :param data:
    :param metadata:
    :return:
    """
    # return (out_fn, 'SUCCESS')
    pass


def main():
    parser = argparse.ArgumentParser(description="BigBrain binarization")
    parser.add_argument('bb_dir', type=str,
                        help=('The folder containing BigBrain NIfTI images'
                              '(local fs only)'))
    parser.add_argument('output_dir', type=str,
                        help=('the folder to save binarized images to '
                              '(local fs only)'))
    parser.add_argument('threshold', type=int, help='binarization threshold')
    parser.add_argument('iterations', type=int, help='number of iterations')
    parser.add_argument('--benchmark', action='store_true',
                        help='benchmark results')
    
    #args = parser.parse_args()
    imgRDD = db.from_sequence(retrieve_input(os.path.abspath('test/data'))) \
        .map(lambda x: read_img(x[0], False, './test', data=x[1]))

    # To test the previous functions
    imgRDD.compute()
    pass


if __name__ == '__main__':
    main()
