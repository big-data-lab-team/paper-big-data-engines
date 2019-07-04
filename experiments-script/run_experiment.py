import subprocess
from random import shuffle
import json


with open("/nfs/paper-big-data-engines/experiments-script/bids.json") as f_in:
    experiments = json.load(f_in)
    shuffle(experiments)
    for exp in experiments:
        experiment = exp["experiment"]
        filename = exp["file"]
        # iterations = str(exp["iterations"])
        # delay = str(exp["delay"])
        # chunks = str(exp["chunks"])

        subprocess.run(
            ["sh", "/nfs/paper-big-data-engines/experiments-script/clear-cache.sh"]
        )

        if experiment[:5] == "spark":
            subprocess.run(
                [
                    "spark-submit",
                    "--master",
                    "spark://192.168.73.10:7077",
                    "--executor-memory",
                    "25G",
                    "--driver-memory",
                    "25G",
                    "/nfs/paper-big-data-engines/bidsApp-examples/" + filename,
                    "/nfs/bids-data/ds005",
                    "/nfs/bids/outputs",
                    experiment,
                    "--benchmark",
                ]
            )
        else:
            subprocess.run(
                [
                    "python",
                    "/nfs/paper-big-data-engines/bidsApp-examples/" + filename,
                    "192.168.73.10:8786",
                    "/nfs/bids-data/ds005",
                    "/nfs/bids/outputs",
                    experiment,
                    "--benchmark",
                ]
            )
