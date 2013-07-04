#!/bin/bash
python codelog.py $@
sn=$(echo "$1" | rev | cut -d '.' -f 2- | rev)
kernprof.py -l $1
python -mline_profiler $sn.lprof > $sn.lprof.txt
statsPrint.py $sn.lprof.txt
python codelog.py clean $@

