from datetime import datetime
import os
import random
import subprocess
import time

REPETITIONS = 1

n_nodes = [2, 4, 8]
n_iterations = [1, 8, 64]
sleep_time = [0.25, 1, 4, 16]

default = {
    "node": n_nodes[1],
    "itr": n_iterations[1],
    "sleep": sleep_time[1],
}

cmd_templates = [
    # 'spark-submit --master spark:// cli.py -i {0} -o {0}-output -s spark:// --benchmark-folder {4} spark {1} {2}',  # TODO set master url once spark is configured
    "benchmark -i {0} -o {0}-output -s slurm -n {3} -b {4} dask {1} {2}",
]

benchmark_folder = os.path.join("/", "home", "mathdugre", "ccpe-output")

BB_5000 = os.path.join(
    "/", "mnt", "lustre", "mathdugre", "datasets", "bigbrain", "nii", "5000_blocks"
)
BB_2500 = os.path.join(
    "/", "mnt", "lustre", "mathdugre", "datasets", "bigbrain", "nii", "2500_blocks"
)
BB_1000 = os.path.join(
    "/", "mnt", "lustre", "mathdugre", "datasets", "bigbrain", "nii", "1000_blocks"
)
BB_blocks = [
    BB_5000,
    # BB_2500,
    # BB_1000,
]

container = os.path.join("/", "home", "mathdugre", "containers", "bids.sif")
CoRR = os.path.join("/", "mnt", "lustre", "mathdugre", "datasets", "CoRR")

cmds = []

for cmd_template in cmd_templates:
    for x in n_nodes:
        cmds.append(
            cmd_template.format(
                BB_5000,
                "increment",
                f"{default['itr']} {default['sleep']}",
                x,
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         BB_5000,
        #         "multi-increment",
        #         f"{default['itr']} {default['sleep']}",
        #         x,
        #         benchmark_folder,
        #     )
        # )
        cmds.append(
            cmd_template.format(
                BB_5000,
                "histogram",
                "",
                x,
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         BB_5000,
        #         "kmeans",
        #         f"{default['itr']}",
        #         x,
        #         benchmark_folder,
        #     )
        # )

    for x in n_iterations:
        cmds.append(
            cmd_template.format(
                BB_5000,
                "increment",
                f"{x} {default['sleep']}",
                default["node"],
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         BB_5000,
        #         "multi-increment",
        #         f"{x} {default['sleep']}",
        #         default["node"],
        #         benchmark_folder,
        #     )
        # )
        cmds.append(
            cmd_template.format(
                BB_5000,
                "histogram",
                "",
                default["node"],
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         BB_5000,
        #         "kmeans",
        #         x,
        #         default["node"],
        #         benchmark_folder,
        #     )
        # )

    for x in sleep_time:
        cmds.append(
            cmd_template.format(
                BB_5000,
                "increment",
                f"{default['itr']} {x}",
                default["node"],
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         BB_5000,
        #         "multi-increment",
        #         f"{default['itr']} {x}",
        #         default["node"],
        #         benchmark_folder,
        #     )
        # )

    for x in BB_blocks:
        cmds.append(
            cmd_template.format(
                x,
                "increment",
                f"{default['itr']} {default['sleep']}",
                default["node"],
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         x,
        #         "multi-increment",
        #         f"{default['itr']} {default['sleep']}",
        #         default["node"],
        #         benchmark_folder,
        #     )
        # )
        cmds.append(
            cmd_template.format(
                x,
                "histogram",
                "",
                default["node"],
                benchmark_folder,
            )
        )
        # cmds.append(
        #     cmd_template.format(
        #         x,
        #         "kmeans",
        #         f"{default['itr']}",
        #         default["node"],
        #         benchmark_folder,
        #     )
        # )

    for x in n_nodes:
        cmds.append(
            cmd_template.format(
                CoRR,
                "bids",
                container,
                x,
                benchmark_folder,
            )
        )

cmds = list(set(cmds)) * REPETITIONS
random.shuffle(cmds)

for cmd in cmds:
    print(f"[{datetime.now()}] Running: {cmd}")
    subprocess.run(cmd, shell=True)
    time.sleep(30)
    print(f"[{datetime.now()}] Done")
