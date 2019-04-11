import os
import socket
import uuid


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
    benchmark_dir = os.path.join(output_dir, 'benchmarks-tmp')
    os.makedirs(benchmark_dir, exist_ok=True)
    
    benchmark_file = os.path.join(benchmark_dir,
                                  "bench-{}-{}.txt".format(experiment,
                                                           uuid.uuid1())
                                  )
    
    node = socket.gethostname()
    bn = os.path.basename(filename)
    
    with open(benchmark_file, 'a+') as f_out:
        # Write
        f_out.write('{0} {1} {2} {3} {4}\n'.format(func_name,
                                                   start,
                                                   end,
                                                   bn,
                                                   node))


def crawl_dir(input_dir):
    """Crawl the input directory to retrieve MINC files.
    
    :param input_dir: str -- representation of the path for the input file.
    :return: list -- of the retrieved path.
    """
    rv = list()
    for folder, subs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.mnc'):
                path = os.path.join(folder, filename)
                rv.append(path)
    return rv
