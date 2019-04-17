import argparse
from time import time
import os

import dask
import dask.bag as db
from dask.distributed import Client
from dask.optimization import fuse

from utils import crawl_dir
from Increment import read_img, increment, save_incremented


if __name__ == '__main__':
    start = time()  # Start time of the pipeline
    
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
    
    cluster = args.scheduler
    client = Client(cluster)
    
    print(client)
    client.upload_file('utils.py')  # Allow workers to use module
    
    # Read images
    paths = crawl_dir(os.path.abspath(args.bb_dir))
    paths = db.from_sequence(paths, npartitions=len(paths))
    img_rdd = paths.map(lambda p: read_img(p,
                                           start=start,
                                           args=args))
    
    # Increment the data n time:
    for _ in range(args.iterations):
        img_rdd = img_rdd.map(lambda x:
                              increment(x,
                                        delay=args.delay,
                                        start=start,
                                        args=args))
    
    # Save the data
    img_rdd = img_rdd.map(lambda x:
                          save_incremented(x,
                                           start=start,
                                           args=args))
    
    img_rdd = dask.optimize(img_rdd,
                            array_optimize=dask.optimization.fuse)[0]
    
    img_rdd.compute()
    
    client.close()
