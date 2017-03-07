#!/usr/bin/env bash
# check_load.sh - Shell script that checks load, intended
# for nagios style monitoring systems
#
# copyright C-Store 2015
# Author Mattis Haase
#
# usage:        check_load.sh loadWarn%OneMin loadCrit%OneMin \
#               loadWarn%FiveMin loadCrit%FiveMin loadWarn%FiveteenMin loadCrit%FiveteenMin
# output: OK/WARNING/CRITICAL check_load - \
# cores: $cores OneMin: $OneMinLoad, FiveMin: $FiveMinLoad, FiveteenMin: $FiveteenMinLoad | \
# OneMin=$OneMinLoad OneMinpct=$OneMinLoadpct FiveMin=$FiveMinLoad FiveMinpct=$FiveMinloadpct \
# FiveteenMin=$FiveteenMinLoad FiveteenMinpct=$FiveteenMinLoadpct
#
# loadpercent here will be defined as the unix load * 100 / NumberOfCores
DefaultWarn=80
DefaultCrit=95

OneMinLoadWarn=${1:-$DefaultWarn}
OneMinLoadCrit=${2:-$DefaultCrit}
FiveMinLoadWarn=${3:-$DefaultWarn}
FiveMinLoadCrit=${4:-$DefaultCrit}
FiveteenMinLoadWarn=${5:-$DefaultWarn}
FiveteenMinLoadCrit=${6:-$DefaultCrit}

OS=$(uname -s)

if [ "${OS}" = "Linux" ]; then
	OneMinLoad=$(cat /proc/loadavg | sed -r 's/\ +/\ /g' | cut -d \  -f 1)
	FiveMinLoad=$(cat /proc/loadavg | sed -r 's/\ +/\ /g' | cut -d \  -f 2)
	FiveteenMinLoad=$(cat /proc/loadavg | sed -r 's/\ +/\ /g' | cut -d \  -f 3)
	numberOfCores=$(grep -c processor /proc/cpuinfo)
elif [ "${OS}" = "FreeBSD" ]; then
	OneMinLoad=$(sysctl -n vm.loadavg | cut -d" " -f 2)
	FiveMinLoad=$(sysctl -n vm.loadavg | cut -d" " -f 3)
	FiveteenMinLoad=$(sysctl -n vm.loadavg | cut -d" " -f 4)
	numberOfCores=$(sysctl -n hw.ncpu)
fi

OneMinLoadpct=$(bc <<< "100*$OneMinLoad/$numberOfCores")
FiveMinLoadpct=$(bc <<< "100*$FiveMinLoad/$numberOfCores")
FiveteenMinLoadpct=$(bc <<< "100*$FiveteenMinLoad/$numberOfCores")

statusString="check_load - cores: $numberOfCores, load: $OneMinLoad,$FiveMinLoad,$FiveteenMinLoad, loadpercent: $OneMinLoadpct,$FiveMinLoadpct,$FiveteenMinLoadpct | cores=$numberOfCores 1mLoad=$OneMinLoad 1mLoadPercent=$OneMinLoadpct 5mLoad=$FiveMinLoad 5mLoadPercent=$FiveMinLoadpct 15mLoad=$FiveteenMinLoad 15mLoadPercent=$FiveteenMinLoadpct"

if      [ "$OneMinLoadpct" -lt "$OneMinLoadWarn" -a "$FiveMinLoadpct" -lt "$FiveMinLoadWarn" -a "$FiveteenMinLoadpct" -lt "$FiveteenMinLoadWarn" ]; then
        echo "OK -  $statusString"
        exit 0
        elif    [ "$OneMinLoadpct" -ge "$OneMinLoadCrit" -o "$FiveMinLoadpct" -ge "$FiveMinLoadCrit" -o "$FiveteenMinLoadpct" -ge "$FiveteenMinLoadCrit" ]; then
                echo "CRITICAL - $statusString"
                exit 2
        elif    [ "$OneMinLoadpct" -ge "$OneMinLoadWarn" -o "$FiveMinLoadpct" -ge "$FiveMinLoadWarn" -o "$FiveteenMinLoadpct" -ge "$FiveteenMinLoadWarn" ]; then
                echo "WARNING - $statusString"
                exit 1
        else
                echo "UNKNOWN - $statusString"
                exit 3
fi
