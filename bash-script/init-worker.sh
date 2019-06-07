#!/bin/bash
while read h
do
    echo 'Initialising worker on '$h
    ssh -f $h 'screen -S worker -dm dask-worker 192.168.73.10:8786'
done < host8.txt
echo 'DONE'
