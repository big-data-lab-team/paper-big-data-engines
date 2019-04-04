import argparse
from time import time, sleep
import os
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
    import nibabel as nib
    
    minc = nib.load(filename)
    img = nib.Nifti1Image(minc.get_data(), affine=minc.affine)
    
    data = img.get_data()
    
    return filename, data, (img.affine, img.header)


@benchmark(ignore=['data', 'metadata'])
def increment(filename, is_benchmarking, output_dir, experiment, start, *,
              data, metadata, iteration, delay):
    """Increment the data of a Nifti image by 1.
    
    :param filename: str -- representation of the path for the input file.
    :param is_benchmarking: boolean -- whether or not the benchmark is  saved.
    :param output_dir: str -- representation of the path for the output file.
    :param data: nifti1Image -- image to manipulate.
    :param metadata: tuple -- of the form (image affine, image header).
    :param iteration: int -- current iteration
    :return: tuple -- of the form (filename, data, (image affine,
    image header), iteration+1).
    :param delay: int -- sleep time for the task
    """
    data += 1
    sleep(delay)
    
    return filename, data, metadata


@benchmark(ignore=['data', 'metadata'])
def save_incremented(filename, is_benchmarking, output_dir, experiment, start,
                     *, data, metadata, iteration):
    """Save a Nifti image.
    
    :param filename: str -- representation of the path for the input file.
    :param is_benchmarking: boolean -- whether or not the benchmark is  saved.
    :param output_dir: str -- representation of the path for the output file.
    :param data: nifti1Image -- image to manipulate.
    :param metadata: tuple -- of the form (image affine, image header).
    :param iteration: int -- current iteration
    :return: tuple -- of the form (f_out, 'SUCCESS')
    """
    bn = os.path.basename(filename[:-3] + 'nii')  # Save in nifti format
    f_out = os.path.join(output_dir, 'inc-{}itr-{}'.format(iteration, bn))
    
    img = nib.Nifti1Image(data, metadata[0], header=metadata[1])
    nib.save(img, f_out)
    
    return f_out, 'SUCCESS'


def main():
    """Execute the incrementation of a Nifti image's data.
    
    :return:
    """
    parser = argparse.ArgumentParser(description="BigBrain incrementation")
    parser.add_argument('scheduler', type=str, help='Scheduler ip and port')
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
    
    # set up local cluster on your laptop
    client = Client(args.scheduler)
    print('connected')
    
    start = time()
    # Read images
    img_rdd = db.from_sequence(crawl_dir(os.path.abspath(args.bb_dir))) \
        .map(lambda path: read_img(path,
                                   args.benchmark,
                                   args.output_dir,
                                   args.experiment,
                                   start)
             ).persist()
    
    # Increment the data n time:
    for itr in range(0, args.iterations):
        img_rdd = img_rdd.map(lambda x: increment(x[0],
                                                  args.benchmark,
                                                  args.output_dir,
                                                  args.experiment,
                                                  start,
                                                  data=x[1],
                                                  metadata=x[2],
                                                  iteration=itr,
                                                  delay=args.delay)
                              ).persist()
    
    img_rdd = img_rdd.map(lambda x: save_incremented(x[0],
                                                     args.benchmark,
                                                     args.output_dir,
                                                     args.experiment,
                                                     start,
                                                     data=x[1],
                                                     metadata=x[2],
                                                     iteration=args.iterations)
                          ).persist()
    img_rdd.compute()
    
    client.close()


if __name__ == '__main__':
    main()
