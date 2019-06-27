import subprocess
import os

directories = []
for root, sub, filename in os.walk('.'):
    if root != '.' and root[2:][0] != '.':
        directories.append(root)
        print('Crawling through ', root)

processes = []
for directory in directories:
    cmd = 'cat {}/* >> /nfs/results/merged-node-1/results-{}.csv'\
        .format(directory, directory[2:])
    print('Merging results for', directory)
    p = subprocess.Popen(cmd, shell=True)
    processes.append(p)

for p in processes:
    p.wait()
