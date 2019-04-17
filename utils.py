import os
import socket
import uuid
import threading


def benchmark(start, end, filename, output_dir, experiment, func_name):
    """
    
    :param start:
    :param end:
    :param filename:
    :param output_dir:
    :param experiment:
    :param func:
    :return:
    """
    benchmark_dir = os.path.join(output_dir, 'benchmarks/' + experiment)
    os.makedirs(benchmark_dir, exist_ok=True)
    
    benchmark_file = os.path.join(benchmark_dir,
                                  "benchmark-{}-{}.txt".format(experiment,
                                                               uuid.uuid1())
                                  )
    
    bn = os.path.basename(filename)
    node = socket.gethostname()
    thread = threading.currentThread().ident
    pid = os.getpid()
    
    with open(benchmark_file, 'a+') as f_out:
        # Write
        f_out.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(func_name,
                                                           start,
                                                           end,
                                                           bn,
                                                           node,
                                                           thread,
                                                           pid))
    
    
def crawl_dir(input_dir):
    """Crawl the input directory to retrieve MINC files.
    
    :param input_dir: str -- representation of the path for the input file.
    :return: list -- of the retrieved path.
    """
    rv = list()
    for folder, subs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.nii'):
                path = os.path.join(folder, filename)
                rv.append(path)
    return rv
