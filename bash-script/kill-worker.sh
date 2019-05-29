#!/bin/bash
while read h
do
    echo 'Killing worker on '$h
    ssh -f $h 'screen -S worker -X quit'
done < host8.txt
echo 'DONE'
