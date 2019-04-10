#!/bin/bash
while read h
do
    ssh $h &>/dev/null << 'EOF'
    sudo mount 192.168.73.23:/nfs /nfs
EOF
done < host40.txt
