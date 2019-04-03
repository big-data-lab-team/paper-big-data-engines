from functools import wraps
from time import time
import os
import socket
import uuid


def benchmark(_func=None, *, ignore=None):
    """Decorator to benchmark a function and write the result to an output file.
    
    The function passed needs the following arguments:
        - filename : path to the input file.
        - is_benchmarking : boolean -- if the benchmark is written to file.
        - output_dir : path where the result are written.
        - start : time of the experiment
        - experiment : name of the experiment executing.
    
    All other function arguments must be passed by key-word.
    
    :param _func: function --  to execute.
    :param ignore: list --  of arguments to ignore when writing to output file.
    :return: value of func_
    """
    
    def benchmark_wrapper(func):
        @wraps(func)
        def wrapper(filename, is_benchmarking, output_dir, experiment, start,
                    *args, **kwargs):
            # Calculate run time
            start_time = time() - start
            value = func(filename, is_benchmarking, output_dir, experiment,
                         start, *args, **kwargs)
            end_time = time() - start
            
            # Write to file if benchmarking
            if is_benchmarking:
                benchmark_dir = os.path.join(output_dir, 'benchmarks-tmp')
                os.makedirs(benchmark_dir, exist_ok=True)
                
                calling_file = func.__globals__['__file__'].split('/')[-1][:-3]
                benchmark_file = os.path.join(
                    benchmark_dir,
                    "bench-{}-{}-{}.txt".format(calling_file, experiment,
                                                uuid.uuid1())
                )
                
                node = socket.gethostname()
                bn = os.path.basename(filename)
                
                with open(benchmark_file, 'a+') as f_out:
                    # Write
                    f_out.write('{0} {1} {2} {3} {4}'.format(func.__name__,
                                                             start_time,
                                                             end_time,
                                                             bn,
                                                             node))
                    # Write optional keyword-arguments
                    if len(kwargs) > 0:
                        for k, v in sorted(kwargs.items()):
                            if k not in ignore:
                                f_out.write(' {}'.format(v))
                    f_out.write('\n')
            
            return value
        
        return wrapper
    
    if _func is None:
        return benchmark_wrapper
    else:
        return benchmark_wrapper(_func)


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
