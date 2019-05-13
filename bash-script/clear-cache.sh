#!/bin/bash

while read h
do
    echo 'Clearing cache on '$h
    ssh $h &>/dev/null << 'EOF'
    sync
    sudo sh -c "/usr/bin/echo 1 > /proc/sys/vm/drop_caches"
EOF
done < host16.txt
echo 'DONE'