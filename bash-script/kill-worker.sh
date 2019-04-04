#!/bin/bash
while read h
do
    ssh $h 'screen -S worker -X quit'
done < host.txt
