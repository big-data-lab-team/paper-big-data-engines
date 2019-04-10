#!/bin/bash
while read h
do
    ssh $h '\x003'
done
