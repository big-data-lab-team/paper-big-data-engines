import os
import random
import subprocess

REPETITIONS = 3

n_nodes = [2, 4, 8]
n_iterations = [8, 64, 512]
sleep_time = [0.125, 1, 8, 64]

default = {
    "node": n_nodes[1],
    "itr": n_iterations[0],
    "sleep": sleep_time[1],
}

cmd_templates = [
    # 'spark-submit --master spark:// cli.py -i {0} -o {0}-output -s spark:// --benchmark spark {1} {2}',  # TODO set master url once spark is configured
    "benchmark -i {0} -o {0} -s slurm -n {3} --benchmark dask {1} {2}",
]

BB_1000 = os.path.join("/", "mnt", "lustre", "mathdugre", "bigbrain-1000")
BB_500 = os.path.join("/", "mnt", "lustre", "mathdugre", "bigbrain-500")
BB_2500 = os.path.join("/", "mnt", "lustre", "mathdugre", "bigbrain-2500")
BB_blocks = [
    # BB_2500,
    BB_1000,
    # BB_500,
]

container = os.path.join("/", "mnt", "lustre", "mathdugre", "containers", "bids.sif")
CoRR = os.path.join("/", "mnt", "lustre", "mathdugre", "CoRR")

cmds = []

for cmd_template in cmd_templates:
    for x in n_nodes:
        cmds.append(
            cmd_template.format(
                BB_1000, "increment", f"{default['itr']} {default['sleep']}", x
            )
        )
        cmds.append(
            cmd_template.format(
                BB_1000, "multi-increment", f"{default['itr']} {default['sleep']}", x
            )
        )
        cmds.append(cmd_template.format(BB_1000, "histogram", "", x))
        cmds.append(cmd_template.format(BB_1000, "kmeans", f"{default['itr']}", x))

    for x in n_iterations:
        cmds.append(
            cmd_template.format(
                BB_1000, "increment", f"{x} {default['sleep']}", default["node"]
            )
        )
        cmds.append(
            cmd_template.format(
                BB_1000, "multi-increment", f"{x} {default['sleep']}", default["node"]
            )
        )
        cmds.append(cmd_template.format(BB_1000, "histogram", "", default["node"]))
        cmds.append(cmd_template.format(BB_1000, "kmeans", x, default["node"]))

    for x in sleep_time:
        cmds.append(
            cmd_template.format(
                BB_1000, "increment", f"{default['itr']} {x}", default["node"]
            )
        )
        cmds.append(
            cmd_template.format(
                BB_1000, "multi-increment", f"{default['itr']} {x}", default["node"]
            )
        )

    for x in BB_blocks:
        cmds.append(
            cmd_template.format(
                x, "increment", f"{default['itr']} {default['sleep']}", default["node"]
            )
        )
        cmds.append(
            cmd_template.format(
                x,
                "multi-increment",
                f"{default['itr']} {default['sleep']}",
                default["node"],
            )
        )
        cmds.append(cmd_template.format(x, "histogram", "", default["node"]))
        cmds.append(
            cmd_template.format(x, "kmeans", f"{default['itr']}", default["node"])
        )

    for x in n_nodes:
        cmds.append(cmd_template.format(CoRR, "bids", container, x))

cmds = list(set(cmds)) * REPETITIONS
random.shuffle(cmds)

for cmd in cmds:
    print("Running:", cmd)
    subprocess.run(cmd, shell=True)
