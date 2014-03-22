#!/bin/bash

for line in `cat $1`
do
    echo "-----------------------------------------------------"
    echo $line
    name=${line/.txt.bz2/}
    python buildpcfg.py ../PasswordDictionary/passwords/$line
    python honey_enc.py ../PasswordDictionary/passwords/$line
    mv logfile.txt testRes/logfile_$name.txt
done
