import argparse
from time import time
import os
import numpy as np
import nibabel as nib
import dask.bag as db
from dask.distributed import Client, LocalCluster
from utils import benchmark, crawl_dir


@benchmark()
def read_img(filename, is_benchmarking, output_dir, experiment, start):
    """Read the image from an MINC format to a Nifti format.
    
    :param filename: str -- representation of the path for the input file.
    :param is_benchmarking: boolean -- whether or not the benchmark is  saved.
    :param output_dir: str -- representation of the path for the output file.
    :return: tuple -- of the form (filename, data, (image affine,
    image header)).
    """
    minc = nib.load(filename)
    img = nib.Nifti1Image(minc.get_data(), affine=minc.affine)
    
    data = img.get_data()
    
    return filename, data, (img.affine, img.header)


@benchmark(ignore=['data', 'metadata', 'threshold'])
def binarize_data(filename, is_benchmarking, output_dir, experiment, start, *,
                  data, metadata, threshold=0.5):
    """Binarize the data.
    
    :param filename: str -- representation of the path for the input file.
    :param is_benchmarking: boolean -- whether or not the benchmark is  saved.
    :param output_dir: str -- representation of the path for the output file.
    :param data: nifti1Image -- image to binarize.
    :param metadata: tuple -- of the form (image affine, image header).
    :param threshold: int --
    :return:
    """
    
    if data.max() == 1:
        threshold = 0
    
    data = np.where(data > threshold, 1, 0)
    
    return filename, data, metadata


@benchmark(ignore=['data', 'metadata'])
def save_binarization(filename, is_benchmarking, output_dir, experiment,
                      start, *, data, metadata):
    """Save the data into a nifti1Image format.
    
    :param filename: str -- representation of the path for the input file.
    :param is_benchmarking: boolean -- whether or not the benchmark is  saved.
    :param output_dir: str -- representation of the path for the output file.
    :param data: nifti1Image -- image to binarize.
    :param metadata: tuple -- of the form (image affine, image header).
    :return:
    """
    img = nib.Nifti1Image(data, metadata[0], header=metadata[1])
    
    bn = os.path.basename(filename[:-3] + 'nii')  # Save in nifti format
    f_out = os.path.join(output_dir, 'bin-' + bn)
    nib.save(img, f_out)
    
    return f_out, 'SUCCESS'


def main():
    """
    
    :return: void
    """
    parser = argparse.ArgumentParser(description="BigBrain binarization")
    parser.add_argument('bb_dir', type=str,
                        help=('The folder containing BigBrain NIfTI images'
                              '(local fs only)'))
    parser.add_argument('output_dir', type=str,
                        help=('the folder to save binarized images to '
                              '(local fs only)'))
    parser.add_argument('experiment', type=str,
                        help='Name of the experiment being performed')
    parser.add_argument('threshold', type=int, help='binarization threshold')
    parser.add_argument('iterations', type=int, help='number of iterations')
    parser.add_argument('--benchmark', action='store_true',
                        help='benchmark results')
    
    args = parser.parse_args()
    
    # set up local cluster on your laptop
    cluster = LocalCluster(n_workers=1, diagnostics_port=8788)
    Client(cluster)
    
    start = time()
    
    # Read images
    img_rdd = db.from_sequence(crawl_dir(os.path.abspath(args.bb_dir))) \
        .map(lambda path: read_img(path,
                                   args.benchmark,
                                   args.output_dir,
                                   args.experiment,
                                   start))
    
    # Binarize the image data
    for i in range(args.iterations):
        img_rdd = img_rdd.map(lambda x: binarize_data(x[0],
                                                      args.benchmark,
                                                      args.output_dir,
                                                      args.experiment,
                                                      start,
                                                      data=x[1],
                                                      metadata=x[2],
                                                      threshold=args.threshold))
    
    # Save the binarized data
    img_rdd = img_rdd.map(lambda x: save_binarization(x[0],
                                                      args.benchmark,
                                                      args.output_dir,
                                                      args.experiment,
                                                      start,
                                                      data=x[1],
                                                      metadata=x[2]))
    
    # Compute above function
    img_rdd.compute()


if __name__ == '__main__':
    main()
