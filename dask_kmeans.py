import argparse
from io import BytesIO
from time import time
import os
import numpy as np
import nibabel as nib
import dask.bag as db
from dask.distributed import Client, LocalCluster
from utils import benchmark, crawl_dir


def get_nearest_centroids(d, c, start, args):
    """
    
    :param d:
    :param c:
    :return:
    """
    
    distance = None
    nearest_c = None

    for centroid in c:
        c_dist = abs(d[0] - centroid)
    
        if (distance is None or c_dist < distance
                or (c_dist == distance
                    and ((d[0] % 2 == 1 and nearest_c < centroid)
                         or (d[0] % 2 == 0 and nearest_c > centroid)))):
            distance = c_dist
            nearest_c = centroid

    return nearest_c, (d[0], d[1])


def update_centroids(d, start, args):
    """
    
    :param d:
    :return:
    """
    # format = list of tuples
    # e.g. [(0, 1), (2, 4), (3, 2)]
    sum_els = float(sum([i[0]*i[1] for i in d]))
    num_els = sum(i[1] for i in d)
    updated = sum_els/num_els

    return updated


def save_segmented(d, assignments, out):
    """
    
    :param d:
    :param assignments:
    :param out:
    :return:
    """
    # read data into nibabel
    fh = nib.FileHolder(fileobj=BytesIO(d[1]))
    im = nib.Nifti1Image.from_file_map({'header': fh, 'image': fh})
    
    data = im.get_data()
    
    assigned_class = [c[0] for c in assignments]
    
    for i in range(0, len(assigned_class)):
        assigned_voxels = [l[0] for c in assignments if
                           c[0] == assigned_class[i] for l in
                           c[1]]  # list(set(assignments[i][1]))
        data[np.where(np.isin(data, assigned_voxels))] = assigned_class[i]
    im_seg = nib.Nifti1Image(data, im.affine)
    
    # save segmented image
    output_file = os.path.join(out, 'classified-' + os.path.basename(d[0]))
    nib.save(im_seg, output_file)
    
    return output_file, "SAVED"


def get_voxels(filename):
    """Read the image from an MINC format to a Nifti format.
    
    :param filename: str -- representation of the path for the input file.
    :return: tuple -- of the form (filename, data, (image affine,
    image header)).
    """
    minc = nib.load(filename)
    img = nib.Nifti1Image(minc.get_data(), affine=minc.affine)
    
    data = img.get_data()
    
    return data.flatten('F')


def main():
    """
    
    :return:
    """
    # mri centroids: 0.0, 125.8, 251.6, 377.4
    start = time()
    
    parser = argparse.ArgumentParser(description="BigBrain k-means"
                                                 " segmentation")
    parser.add_argument('scheduler', type=str, help="scheduler ip and port")
    parser.add_argument('bb_dir', type=str, help="The folder containing "
                                                 "BigBrain NIfTI images (local"
                                                 " fs only)")
    parser.add_argument('output_dir', type=str, help="the folder to save "
                                                     "segmented images to "
                                                     "(local fs only)")
    parser.add_argument('experiment', type=str,
                        help='Name of the experiment being performed')
    parser.add_argument('iterations', type=int, help="maximum number of kmean "
                                                     "iterations")
    parser.add_argument('centroids', type=float, nargs='+',
                        help="cluster centroids")
    parser.add_argument('--benchmark', action='store_true',
                        help='Benchmark pipeline')
    
    args = parser.parse_args()

    # cluster = args.scheduler  # Cluster scheduler
    cluster = LocalCluster(n_workers=1, diagnostics_port=8788)  # Local cluster
    client = Client(cluster)
    print(client)
    
    centroids = args.centroids
    
    files = db.from_sequence(crawl_dir(os.path.abspath(args.bb_dir)))
    
    files = client.scatter(files)
    voxel_futures = client.map(get_voxels, files)
    voxel_arrays = client.gather(voxel_futures)
    voxels = client.persist(voxel_arrays.reshape(-1))

    c_changed = True
    count = 0
    assignments = None

    def key(x):
        return x[0]

    def binop(total, x):
        return total + x[1]

    def combine(x, y):
        return x + y

    
    
    # assignment = voxel_rdd.map(lambda x: (x, 1)) \
    #     .foldby(key, binop, 0, combine, 0)\
    #     .map(lambda x: get_nearest_centroids(x, centroids))


if __name__ == '__main__':
    main()
