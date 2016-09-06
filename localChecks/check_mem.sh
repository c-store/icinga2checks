#!/bin/bash
# check_mem.sh - Shell script that checks memory and swap
# for nagios style monitoring systems
#
# copyright C-Store 2015
#
# usage:        check_mem.sh
# output: OK/WARNING/CRITICAL check_mem - used ram: $usedram, max ram: $maxram, used ram percent: $usedrampctWithBuffers, buffers: $buffers, cached: $cached, used swap: $usedSwap, max Swap: $maxSwap, used swap %: $usedSwappct | usedram=$usedram maxram=$maxram usedramPercent=$usedrampctWithBuffers buffers=$buffers cached=$cached usedSwap=$usedSwap maxSwap=$maxSwap usedSwappercent=$usedSwappct"
DefaultramWarn=90
DefaultramCrit=95
DefaultswapWarn=80
DefaultSwapCrit=90

ramWarn=${1:-$DefaultramWarn}
ramCrit=${2:-$DefaultramCrit}
swapWarn=${3:-$DefaultswapWarn}
swapCrit=${4:-$DefaultSwapCrit}

maxram=$(free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 2)
usedram=$(free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 3)
freeram=$(free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 4)
buffers=$(free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 6)
cached=$(free -m | grep Mem | sed -r 's/\ +/\ /g' | cut -d \  -f 7)

maxSwap=$(free -m | grep Swap | sed -r 's/\ +/\ /g' | cut -d \  -f 2)
usedSwap=$(free -m | grep Swap | sed -r 's/\ +/\ /g' | cut -d \  -f 3)
freeSwap=$(free -m | grep Swap | sed -r 's/\ +/\ /g' | cut -d \  -f 4)

usedrampct=$(echo $(( ((($usedram-buffers)-cached) * 100) / $maxram )))
usedrampctWithBuffers=$(echo $(( ($usedram * 100) / $maxram )))
if [ "$usedSwap" -eq "0" ]; then
        usedSwappct=0
else
        usedSwappct=$(echo $(( ($usedSwap * 100) / $maxSwap )))
fi

statusString="check_mem - used ram: $usedram, max ram: $maxram, used ram percent: $usedrampctWithBuffers, buffers: $buffers, cached: $cached, used swap: $usedSwap, max Swap: $maxSwap, used swap %: $usedSwappct | usedram=$usedram maxram=$maxram usedramPercent=$usedrampctWithBuffers buffers=$buffers cached=$cached usedSwap=$usedSwap maxSwap=$maxSwap usedSwappercent=$usedSwappct"

if      [ "$usedrampct" -lt "$ramWarn" ] && [ "$usedSwappct" -lt "$swapWarn" ]; then
        echo "OK - $statusString"
        exit 0
        elif    [ "$usedrampct" -gt "$ramCrit" ] || [ "$usedrampct" -eq "$ramCrit" ] || [ "$usedSwappct" -gt "$swapCrit" ] || [ "$usedSwappct" -eq "$swapCrit" ]; then
                echo "CRITICAL - $statusString"
                exit 2
        elif    [ "$usedrampct" -gt "$ramWarn" ] || [ "$usedrampct" -eq "$ramWarn" ] || [ "$usedSwappct" -gt "$swapWarn" ] || [ "$usedSwappct" -eq "$swapWarn" ]; then
                echo "WARNING - $statusString"
                exit 1
        else
                echo "UNKNOWN - $statusString"
                exit 3
fi
