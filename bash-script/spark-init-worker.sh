#!/bin/bash

while read h
do
    echo 'Starting worker on '$h
    ssh -f $h 'sbin/start-slaves.sh'
done < host40.txt
echo 'DONE'
