from datetime import datetime
import os
import random
import subprocess
import time


REPETITIONS = 10

n_nodes = [2, 4, 8]
n_iterations = [1, 5, 25]
n_iterations_small = [1, 3, 9]
BB_blocks = [1000, 2500, 5000]

default = {
    "node": n_nodes[1],
    "itr": n_iterations[1],
    "small_itr": n_iterations_small[1],
    "sleep": 1,
}

cmd_templates = [
    "SLURM_NNODES={3} program='projects/paper-big-data-engines/src/cli.py -i {0} -o {0}-output -s slurm -n {3} -b {4} spark {1} {2}' ./projects/paper-big-data-engines/deploy_spark_cluster.sh",
    "benchmark -i {0} -o {0}-output -s slurm -n {3} -b {4} dask {1} {2}",
]

benchmark_folder = os.path.join("/", "home", "mathdugre", "ccpe-output")
os.makedirs(benchmark_folder, exist_ok=True)

BB_path = lambda x: os.path.join(
    "/", "mnt", "lustre", "mathdugre", "datasets", "bigbrain", "nii", f"{x}_blocks"
)
BB_sample_path = lambda x: os.path.join(
    "/", "mnt", "lustre", "mathdugre", "datasets", "bigbrain", "nii", f"{x}_blocks-sample"
)


container = os.path.join("/", "home", "mathdugre", "containers", "bids.sif")
CoRR = os.path.join("/", "mnt", "lustre", "mathdugre", "datasets", "CoRR")

cmds = []

for cmd_template in cmd_templates:
    for x in n_nodes:
        cmds.append(
            cmd_template.format(
                BB_path(5000),
                "increment",
                f"{5000} {default['itr']} {default['sleep']}",
                x,
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_sample_path(5000),
                "multi-increment",
                f"{5000} {default['small_itr']} {default['sleep']}",
                x,
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_sample_path(5000),
                "kmeans",
                f"{5000} {default['small_itr']}",
                x,
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_path(5000),
                "histogram",
                f"{5000}",
                x,
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                CoRR,
                "bids",
                container,
                x,
                benchmark_folder,
            )
        )

    for n in BB_blocks:
        cmds.append(
            cmd_template.format(
                BB_path(n),
                "increment",
                f"{n} {default['itr']} {default['sleep']}",
                default["node"],
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_sample_path(n),
                "multi-increment",
                f"{n} {default['small_itr']} {default['sleep']}",
                default["node"],
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_sample_path(n),
                "kmeans",
                f"{n} {default['small_itr']}",
                default["node"],
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_path(n),
                "histogram",
                f"{n}",
                default["node"],
                benchmark_folder,
            )
        )

    for x in n_iterations:
        cmds.append(
            cmd_template.format(
                BB_path(5000),
                "increment",
                f"{5000} {x} {default['sleep']}",
                default["node"],
                benchmark_folder,
            )
        )
    for x in n_iterations_small:
        cmds.append(
            cmd_template.format(
                BB_sample_path(5000),
                "multi-increment",
                f"{5000} {x} {default['sleep']}",
                default["node"],
                benchmark_folder,
            )
        )
        cmds.append(
            cmd_template.format(
                BB_sample_path(5000),
                "kmeans",
                f"{5000} {x}",
                default["node"],
                benchmark_folder,
            )
        )

cmds = list(set(cmds)) * REPETITIONS
random.shuffle(cmds)

total_cmds = len(cmds)
for i, cmd in enumerate(cmds, 1):
    print(f"[{datetime.now()}] -- ({i}/{total_cmds}) -- Running : {cmd}")
    subprocess.run("sudo /home/shared/dropcache_compute.sh", shell=True)
    subprocess.run(cmd, shell=True)
    time.sleep(10)
    print(f"[{datetime.now()}] Done")
