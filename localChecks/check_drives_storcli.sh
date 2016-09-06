#!/bin/bash
# check_drives_storcli.sh - Shell script that checks drive health
# intended for storcli
# for nagios style monitoring systems
#
# copyright C-Store 2015
#
# usage:        check_mem.sh 
# output: OK/WARNING/CRITICAL check_srives_storecli - d0: 1/0, d0errors:0, .... dn: 1/0, dnerrors:0 | d0:1/0,d0errors:n,... 

output="$(/opt/lsi/storcli/storcli /c0 /eall /sall show all)"
maxRAM=`free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 2`
usedRAM=`free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 3`
freeRAM=`free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 4`
buffers=`free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 6`
cached=`free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 7`

maxSwap=`free -m | grep Swap | sed -r 's/\ +/\ /g' | cut -d \  -f 2`
usedSwap=`free -m | grep Swap | sed -r 's/\ +/\ /g' | cut -d \  -f 3`
freeSwap=`free -m | grep Swap | sed -r 's/\ +/\ /g' | cut -d \  -f 4`

usedRAMpct=`echo $(( ((($usedRAM-buffers)-cached) * 100) / $maxRAM ))`
usedRAMpctWithBuffers=`echo $(( ($usedRAM * 100) / $maxRAM ))`
if [ "$usedSwap" -eq "0" ]; then
        usedSwappct=0
else
        usedSwappct=`echo $(( ($usedSwap * 100) / $maxSwap ))`
fi

statusString="check_mem - used RAM: $usedRAM, max RAM: $maxRAM, used RAM percent: $usedRAMpctWithBuffers, buffers: $buffers, cached: $cached, used swap: $usedSwap, max Swap: $maxSwap, used swap %: $usedSwappct | usedRAM=$usedRAM maxRAM=$maxRAM usedRAMPercent=$usedRAMpctWithBuffers buffers=$buffers cached=$cached usedSwap=$usedSwap maxSwap=$maxSwap usedSwappercent=$usedSwappct"

if      [ "$usedRAMpct" -lt "$ramWarn" -a "$usedSwappct" -lt "$swapWarn" ]; then
        echo "OK - $statusString"
        exit 0
        elif    [ "$usedRAMpct" -gt "$ramCrit" -o "$usedRAMpct" -eq "$ramCrit" -o "$usedSwappct" -gt "$swapCrit" -o "$usedSwappct" -eq "$swapCrit" ]; then
                echo "CRITICAL - $statusString"
                exit 2
        elif    [ "$usedRAMpct" -gt "$ramWarn" -o "$usedRAMpct" -eq "$ramWarn" -o "$usedSwappct" -gt "$swapWarn" -o "$usedSwappct" -eq "$swapWarn" ]; then
                echo "WARNING - $statusString"
                exit 1
        else
                echo "UNKNOWN - $statusString"
                exit 3
fi
