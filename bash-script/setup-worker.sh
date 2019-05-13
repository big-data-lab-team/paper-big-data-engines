#!/bin/bash
while read h
do
    ssh $h &>/dev/null << 'EOF'
    sudo mount 192.168.73.10:/nfs /nfs
EOF
done < host16.txt
