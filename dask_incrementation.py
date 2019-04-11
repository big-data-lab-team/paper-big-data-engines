import argparse
from time import time, sleep
import os

import nibabel as nib
import dask.bag as db
from dask.distributed import Client, LocalCluster
import numpy as np

from utils import benchmark, crawl_dir


def read_img(filename, start, args):
    """Read the image from an MINC format to a Nifti format.
    
    :param filename: str -- representation of the path for the input file.
    :return: tuple -- of the form (filename, data, (image affine,
    image header)).
    """
    start_time = time() - start
    
    minc = nib.load(filename)
    img = nib.Nifti1Image(minc.get_data(), affine=minc.affine)
    data = img.get_data()
    
    end_time = time() - start
    
    if args.benchmark:
        benchmark(start_time, end_time, filename, args.output_dir,
                  args.experiment, read_img.__name__)
    
    return filename, data, (img.affine, img.header)


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
        benchmark(start_time, end_time, filename, args.output_dir,
                  args.experiment, increment.__name__)
    
    return filename, data, metadata


def save_incremented(img_rdd, start, args):
    """Save a Nifti image.
    
    :param filename: str -- representation of the path for the input file.
    :param data: nifti1Image -- image to manipulate.
    :param metadata: tuple -- of the form (image affine, image header).
    :return: tuple -- of the form (f_out, 'SUCCESS')
    """
    start_time = time() - start
    
    filename = img_rdd[0]
    data = img_rdd[1]
    metadata = img_rdd[2]
    
    bn = os.path.basename(filename[:-3] + 'nii')  # Save in nifti format
    f_out = os.path.join(args.output_dir,
                         '{}-{}'.format(args.experiment, bn))
    
    img = nib.Nifti1Image(data, metadata[0], header=metadata[1])
    nib.save(img, f_out)
    
    end_time = time() - start
    
    if args.benchmark:
        benchmark(start_time, end_time, filename, args.output_dir,
                  args.experiment, save_incremented.__name__)
    
    return f_out, 'SUCCESS'


if __name__ == '__main__':
    """Execute the incrementation of a Nifti image's data.
    
    :return:
    """
    parser = argparse.ArgumentParser(description="BigBrain incrementation")
    parser.add_argument('scheduler', type=str,
                        help='Scheduler ip and port')
    parser.add_argument('bb_dir', type=str,
                        help=('The folder containing BigBrain NIfTI images'
                              '(local fs only)'))
    parser.add_argument('output_dir', type=str,
                        help=('the folder to save incremented images to'
                              '(local fs only)'))
    parser.add_argument('experiment', type=str,
                        help='Name of the experiment being performed')
    parser.add_argument('iterations', type=int, help='number of iterations')
    parser.add_argument('delay', type=float, help='sleep delay during '
                                                  'incrementation')
    parser.add_argument('--benchmark', action='store_true',
                        help='benchmark results')
    
    args = parser.parse_args()
    
    # cluster = args.scheduler  # Cluster scheduler
    cluster = LocalCluster(n_workers=1, diagnostics_port=8788)  # Local cluster
    client = Client(cluster)
    print(client)
    
    start = time()  # Start time of the pipeline
    
    # Read images
    files = db.from_sequence(crawl_dir(os.path.abspath(args.bb_dir)))
    img_rdd = client.map(read_img, files, start=start, args=args)
    
    # Increment the data n time:
    for _ in range(0, args.iterations):
        img_rdd = client.map(increment,
                             img_rdd,
                             delay=args.delay,
                             start=start,
                             args=args)
    
    # Save the data
    img_rdd = client.map(save_incremented, img_rdd, start=start, args=args)
    client.gather(img_rdd)
    
    client.close()
