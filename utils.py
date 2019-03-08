from functools import wraps
from time import perf_counter
import os
import socket
import uuid


def benchmark(_func=None, *, ignore=None):
    """Decorator to benchmark a function and write the result to an output file.
    
    The function passed needs the following arguments:
        - filename : path to the input file.
        - is_benchmarking : boolean -- if the benchmark is written to file.
        - output_dir : path where the result are written.
    
    All other function arguments must be passed by key-word.
    
    :param _func: function to execute.
    :param ignore: list of arguments to ignore when writing to output file.
    :return: value of func_
    """
    def benchmark_wrapper(func):
        @wraps(func)
        def wrapper(filename, is_benchmarking, output_dir, *args,
                    **kwargs):
            # Calculate run time
            start_time = perf_counter()
            value = func(filename, is_benchmarking, output_dir,
                         *args, **kwargs)
            end_time = perf_counter()
            run_time = end_time - start_time
            
            # Write to file if benchmarking
            if is_benchmarking:
                benchmark_dir = os.path.join(output_dir, 'benchmarks')
                os.makedirs(benchmark_dir, exist_ok=True)
                
                benchmark_file = os.path.join(
                    benchmark_dir,
                    "bench-{}.txt".format(str(uuid.uuid1()))
                )
                
                node = socket.gethostname()
                bn = os.path.basename(filename)
                
                with open(benchmark_file, 'a+') as f_out:
                    # Write
                    f_out.write('{0} {1} {2} {3}'.format(func.__name__,
                                                         run_time,
                                                         bn,
                                                         node))
                    # Write optional keyword-arguments
                    if len(kwargs) > 0:
                        for k, v in kwargs.items():
                            if k not in ignore:
                                f_out.write(' {}'.format(v))
                    f_out.write('\n')
            
            return value
        
        return wrapper
    
    if _func is None:
        return benchmark_wrapper
    else:
        return benchmark_wrapper(_func)
