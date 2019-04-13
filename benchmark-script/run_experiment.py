import subprocess
from random import shuffle
import json

delay = [2.4, 3.44, 7.68, 320]
chunks = [30, 125, 750]
itr = [1, 10, 100]

with open('experiment.json') as f_in:
    experiments = json.load(f_in)
    shuffle(experiments)
    for exp in experiments:
        experiment = exp['experiment']
        file = exp['file']
        iterations = str(exp['iterations'])
        delay = str(exp['delay'])
        chunks = str(exp['chunks'])
        
        if experiment == 'spark_inc-baseline':
            subprocess.call(['python',
                             '../' + file,
                             '/nfs/bb-' + chunks + 'chunks',
                             '/nfs/results',
                             experiment,
                             iterations,
                             delay,
                             '--benchmark'])
        else:
            subprocess.call(['python',
                             '../' + file,
                             '192.168.73.23:8786',
                             '/nfs/bb-' + chunks + 'chunks',
                             '/nfs/results',
                             experiment,
                             iterations,
                             delay,
                             '--benchmark'])
