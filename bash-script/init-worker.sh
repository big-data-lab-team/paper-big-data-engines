#!/bin/bash
while read h
do
    echo 'Starting worker on '$h
    ssh -f $h 'screen -S worker -dm dask-worker 192.168.73.23:8786 --nprocs 5 --nthreads 1 --resources "process=1"'
done < host.txt
echo 'DONE'
