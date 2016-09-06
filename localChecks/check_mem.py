#!/usr/bin/python3
# check_mem.py - Check Swap and RAM on linux systems
# if warning or critical stage are reached, displays top processes from ps,
# sorted by memory utilization
# for nagios style monitoring systems
#
# copyright C-Store 2016
# Author Mattis Haase, Leon Kühn
#
# usage: check_mem.py -w ramWarnPct -c ramCritPct -W swapWarnPct -C swapCritPct
# output: 
#  If OK:
#  OK - check_mem -

#  If WARNING or CRITICAL:
#  WARNING/CRITICAL - check_mem - 
#  root    1354  0.0  3.2 124112 33244 ?   Ssl  Jun09  10:17 /usr/bin/ruby /
#  nagios  5753  0.9  2.3 1316492 24296 ?  Ssl  Sep05  10:16 /usr/lib/x86_64
#
# perfdata:
# installedram, usedram, freeram, sharedram, buffers\
#    cached, ramnobuffers, ramfreewithcache, installedswap, usedswap\
#    freeswap, usedrampct, usedramnobufferspct, usedswappct

from subprocess import check_output
import re
import sys
import argparse

def parsePs():
    psOutput = check_output(["ps", "aux", "--sort", "-rss"]).decode('utf-8')
    return(psOutput.split('\n', 2)[1])

def parseFree():
    freeOutput = check_output(["free", "m"]).decode('utf-8')
    reg = re.compile('([0-9]+)')
    result = reg.findall(freeOutput)

    freeValues = {
        'maxRam':int(result[0]),
        'usedRam':int(result[1]),
        'freeRam':int(result[2]),
        'shared':int(result[3]),
        'buffers':int(result[4]),
        'cached':int(result[5]),
        'usedRamNoBuffers':int(result[6]),
        'freeRamWithCache':int(result[7]),
        'maxSwap':int(result[8]),
        'usedSwap':int(result[9]),
        'freeSwap':int(result[10])
    }
    freeValues['usedRamPct'] = int(freeValues['usedRam'] / freeValues['maxRam'] * 100)
    freeValues['usedRamPctNoBuffers'] = int(freeValues['usedRamNoBuffers'] / freeValues['maxRam'] * 100)
    freeValues['usedSwapPct'] = int(freeValues['usedSwap'] / freeValues['maxSwap'] * 100)

    return(freeValues)

def main():
    parser = argparse.ArgumentParser(description='Check RAM and Swap.')
    parser.add_argument(
        '-w',
        '--ramwarn',
        help='integer Percentage of RAM used that leads to warning default 90',
        default = 90,
        type = int
    )
    parser.add_argument(
        '-c',
        '--ramcrit',
        help='integer Percentage of RAM used that leads to critical default 95',
        default = 95,
        type = int
    )
    parser.add_argument(
        '-W',
        '--swapwarn',
        help='integer Percentage of swap used that leads to warning default 60',
        default = 60,
        type = int
    )
    parser.add_argument(
        '-C',
        '--swapcrit',
        help='integer Percentage of swap used that leads to critical default 80',
        default = 80,
        type = int
    )
    arguments = parser.parse_args()

    values = parseFree()
    perfdata = "installedram={} usedram={} freeram={} sharedram={}"
    perfdata += " buffers={} cached={} ramnobuffers={} ramfreewithcache={} installedswap={}"
    perfdata += " usedswap={} freeswap={} usedrampct={} usedramnobufferspct={} usedswappct={}"
    perfdata = perfdata.format(
        values['maxRam'],
        values['usedRam'],
        values['freeRam'],
        values['shared'],
        values['buffers'],
        values['cached'],
        values['usedRamNoBuffers'],
        values['freeRamWithCache'],
        values['maxSwap'],
        values['usedSwap'],
        values['freeSwap'],
        values['usedRamPct'],
        values['usedRamPctNoBuffers'],
        values['usedSwapPct']
    )
    psOutput = parsePs()
    if values['usedRamPctNoBuffers'] < arguments.ramwarn and values['usedSwapPct'] < arguments.swapwarn:
        print('OK - check_mem - | ' + perfdata)
        sys.exit(0)
    elif values['usedRamPctNoBuffers'] >= arguments.ramcrit or values['usedSwapPct'] >= arguments.swapcrit:
        print('CRITICAL - ' + psOutput + ' | ' + perfdata)
        sys.exit(2)
    elif values['usedRamPctNoBuffers'] >= arguments.ramwarn or values['usedSwapPct'] >= arguments.swapwarn:
        print('WARNING - ' + psOutput)
        sys.exit(1)
    else:
        print('UNKNOWN - ' + psOutput + ' | ' + perfdata)
        sys.exit(3)
        
if __name__ == "__main__":
    main()
