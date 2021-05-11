#!/usr/bin/env bash

export NODE_MEM=232 # Convert to GiB
export NODE_NPROC=64
export NWORKERS=8

export TOTAL_WORKERS=$(( ${NWORKERS} * ${SLURM_NNODES} ))
export WORKER_NPROC=$(( ${NODE_NPROC} / ${NWORKERS} ))
export WORKER_MEM="$(( ${NODE_MEM} / ${NWORKERS} ))G"

term_handler()
{
    kill $workers_pid
    ${SPARK_HOME}/sbin/stop-master.sh

    exit -1
}
trap 'term_handler' TERM

batch_program()
{
    ${SPARK_HOME}/sbin/start-master.sh
    while [ -z "$MASTER_URL" ]
    do
            MASTER_URL=$(curl -s http://localhost:8080/json/ | jq -r ".url")
            echo "master not found"
            sleep 5
    done
    export MASTER_URL

    SPARK_WORKER_INSTANCES=${NWORKERS} SPARK_NO_DAEMONIZE=1 srun -n ${TOTAL_WORKERS} -N ${SLURM_NNODES} ${SPARK_HOME}/sbin/start-worker.sh -m ${WORKER_MEM} -c ${WORKER_NPROC} ${MASTER_URL} &
    workers_pid=$!

    if [ ! -z "$program" ]
    then
       SPARK_NO_DAEMONIZE=1 ${SPARK_HOME}/bin/spark-submit --master ${MASTER_URL} --driver-memory 32G --executor-memory ${WORKER_MEM} $program
    fi

    kill $workers_pid
    ${SPARK_HOME}/sbin/stop-master.sh
}

batch_program &
wait $!

