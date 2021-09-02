from glob import glob
import os

folders = glob("results/benchmarks/*")

for folder in folders:
    os.rename(folder, folder.replace("'", ""))
