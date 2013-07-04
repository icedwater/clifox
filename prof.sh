#!/bin/bash
if [ $1 == "clean" ]
then
sn=$(echo "$2" | rev | cut -d '.' -f 2- | rev)
rm $sn*prof*
exit 0
fi
python codelog.py $@
sn=$(echo "$1" | rev | cut -d '.' -f 2- | rev)
kernprof.py -l $1
python -mline_profiler $sn.lprof > $sn.lprof.txt
python statsPrint.py $sn.lprof.txt > $sn.profileResults.txt
python codelog.py clean $@
nano -w $sn.profileResults.txt
