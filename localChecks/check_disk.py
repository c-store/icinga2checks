#!/usr/bin/python3
# check_disk.py - Python script that checks hard drive utliization
# for nagios style monitoring systems
#
# copyright C-Store 2016
# Author Mattis Haase
#
# usage:  check_disk.py -w <warn Percent> -c <crit Percent> -f <partition that should be checked>
# output: 
# check_disk.py OK - 
# udev mounted on: /dev
# tmpfs mounted on: /run
# /dev/dm-0 mounted on: /
# /dev/sda1 mounted on: /boot
# 192.168.175.1:/mnt/freenas/backup mounted on: /mnt/backup
#
# perfdata:
# /boot_BlocksAvailable	187,356.00
# /boot_BlocksUsed	41,175.00
# /boot_BlocksTotal	240,972.00
# /boot_PercentUsed	19.00

import argparse
import re
from sys import exit
from subprocess import check_output

def executedf():
    """
    Executes df command
    Returns:
        lOutput = [
            {
                sName           :'partition1',
                iBlocksTotal    :1234,
                iBlocksUsed     :1000
                iBlocksAvailable:234
                iPercent        :90
                sMountpoint     :'/mnt'
            }
        ]
    """
    sDfOutput = check_output(['df']).decode('utf-8')
    lDfOutput = sDfOutput.split('\n')
    lOutput = []

    for i, sLine in enumerate(lDfOutput):
        if not i == 0 and sLine:
            lValues = sLine.split()

            if not lValues[0] == 'none':
                lOutput.append(
                    {
                        'sName'           : lValues[0],
                        'iBlocksTotal'    : lValues[1],
                        'iBlocksUsed'     : lValues[2],
                        'iBlocksAvailable': lValues[3],
                        'iPercent'        : int(lValues[4].replace('%', '')),
                        'sMountpoint'     : lValues[5]
                    }
                )
    return(lOutput)

def compileOutput(lOutput):
    """
    compiles perfdata and output
    gets:
     lOutput: list of dicts for each Disk
    returns:
     complete output without OK/WARNING/CRITICAL
    """
    sPerfdata     = ''
    sNonPerfdata  = ''

    for dPartition in lOutput:
        sPerfdata += ' {0}_BlocksTotal={1} {0}_BlocksUsed={2} {0}_BlocksAvailable={3} {0}_PercentUsed={4}'
        sPerfdata = sPerfdata.format(
            dPartition['sMountpoint'],
            dPartition['iBlocksTotal'],
            dPartition['iBlocksUsed'],
            dPartition['iBlocksAvailable'],
            dPartition['iPercent']
        )
        sNonPerfdata += '\\n{0} mounted on: {1}'
        sNonPerfdata = sNonPerfdata.format(
            dPartition['sName'],
            dPartition['sMountpoint']
        )
    
    sOutput = '{} | {}'.format(sNonPerfdata, sPerfdata)
    return(sOutput)

def compileStatus(lOutput, iWarning, iCritical, sFilesystem):
    """
    compiles OK/WARNING/CRITICAL/UNKNOWN status
    gets:
     lOutput  : list of dicts for each Disk
     iWarning   : warning threshold
     iCritical  : critical threshold
     sFilesystem: filesystem which to compare iWarning and iCritical against
    returns:
     OK/WARNING/CRITICAL/UNKNOWN
    """
    for dPartition in lOutput:
        if sFilesystem == dPartition['sName'] or sFilesystem == dPartition['sMountpoint']:
            if dPartition['iPercent'] >= iCritical: 
                return('CRITICAL')
            elif dPartition['iPercent'] >= iWarning: 
                return('WARNING')
            elif dPartition['iPercent'] < iCritical and dPartition['iPercent'] < iWarning:
                return('OK')
            else:
                return('UNKNOWN')

def main():
    parser = argparse.ArgumentParser(description='Check Disk Space')
    parser.add_argument('-w', '--warning', type=int, help='WARNING Level [%]')
    parser.add_argument('-c', '--critical', type=int, help='CRITICAL level [%]')
    parser.add_argument('-f', '--filesystem', type=str, help='Filesystem which should raise alerts.')

    args = parser.parse_args()

    lOutput = executedf()
    sOutput = compileOutput(lOutput)
    sStatus = compileStatus(
        lOutput=lOutput,
        iWarning=args.warning,
        iCritical=args.critical,
        sFilesystem=args.filesystem
    )

    sOutput = 'check_disk.py {0} - {1}'.format(
        sStatus,
        sOutput
    )

    print(sOutput)

    if sStatus == 'OK':
        exit(0)
    elif sStatus == 'WARNING':
        exit(1)
    elif sStatus == 'CRITICAL':
        exit(2)
    else:
        exit(3)

if __name__ == "__main__":
    main()
