#!/bin/bash
while read h
do
    echo "Setting up worker on "$h
    cat id_rsa.pub | ssh $h 'cat >> ~/.ssh/authorized_keys'  # Put the id_rsa.pub in the same parent folder as this script.
    ssh $h &>/dev/null << 'EOF'
    sudo mount 192.168.73.10:/nfs /nfs
EOF
    ssh -f $h "echo 'export SPARK_HOME=/nfs/spark' >> .bashrc"
done < host8.txt
echo "DONE"
