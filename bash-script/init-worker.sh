#!/bin/bash
while read h
do
    ssh -f $h 'screen -S worker -dm dask-worker 192.168.73.23:8786'
done < host.txt
