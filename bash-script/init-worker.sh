#!/bin/bash
while read h
do
    echo 'Starting worker on '$h
    ssh -f $h 'screen -S worker -dm dask-worker 192.168.73.23:8786'
done < host40.txt
echo 'DONE'
