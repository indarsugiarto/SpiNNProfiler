#! /bin/bash
# Put the freq in the argument
./setFreq.py -p 1 -f $1 -x 0 -y 0
./setFreq.py -p 1 -f $1 -x 0 -y 1
./setFreq.py -p 1 -f $1 -x 1 -y 0
./setFreq.py -p 1 -f $1 -x 1 -y 1
