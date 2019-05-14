#!/bin/bash

while read h
do
    echo 'Clearing cache on '$h
    ssh $h &>/dev/null << 'EOF'
    sync
    sudo sh -c "/usr/bin/echo 1 > /proc/sys/vm/drop_caches"
EOF
done < /nfs/SOEN-499-Project/experiments-script/host8.txt
echo 'DONE'