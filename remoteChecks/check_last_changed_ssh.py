#!/usr/bin/python3
# check_last_changed_ssh.py - Python script that checks last change date of 
# single file, or newest / oldest last change date of all files in folder
#
# copyright C-Store 2016
# Author Mattis Haase
#

import argparse, sys, os
from time import time
from sys import exit

import lib.sshcommand

def parse(lDates, sMode):
    """
    Calculates time difference for all files to today, in days
    Gets: 
      lDates: ['1213125', '1232153473']
    Returns: 
      deltaTime for oldest or youngest file date
    """
    lDelta = []
    
    for i, sDate in enumerate(lDates):
        lDelta.append(float(time()) - int(sDate))
    
    if sMode == 'oldest':
        return int(max(lDelta) / 86400)
    elif sMode == 'youngest':
        return int(min(lDelta) / 86400)
    
def check(sUsername, sHostname, sPath, bRecursive, bBSD):
    """
    Performs check
    Gets: 
      sUsername: SSH username
      sHostname: Hostname of remote machine
      sPath:     Path to folder
      bRecursive: True if folder should be checked recursively
      
    Returns:
      List of seconds since epoch since last change
    """
    SSHCommand = lib.sshcommand.SSHCommand
    lLogin = ['{}@{}'.format(sUsername, sHostname)]
    #displays seconds since epoch for all files
    if '"' not in sPath:
        sPath = '"' + sPath + '"'
    if bRecursive:
        sFindCommand = 'find -type f'
    elif not bRecursive:
        sFindCommand = 'find -maxdepth 1 -type f'
    lFindCommand = sFindCommand.split(' ')
    lFindCommand.insert(1, sPath)
    if bBSD:
        sExecCommand = '-exec stat -f %m "{}" +'
    elif not bBSD:
        sExecCommand = '-exec stat -c \'%Y\' "{}" \;'
    lExecCommand = sExecCommand.split(' ')
    lCommand = lFindCommand + lExecCommand
    lCommand = lLogin + lCommand
    return SSHCommand.execute(SSHCommand, lCommand)
    
def printResult(iDelta, iWarn, iCrit, sMode):
    """
    Prints check results, terminates program.
    Gets:
      iDelta: biggest/smallest Timedelta in days
      iWarn : days before WARNING
      iCrit : days before CRITICAL
      sMode : (oldest|youngest)
    Returns:
      prints result to stdout
    """
    iExitcode = 3
    if iDelta >= iCrit:
        sResult = 'CRITICAL check_last_changed_ssh.py the {} file was modified {} days ago'.format(sMode, iDelta)
        iExitcode = 2
    elif iDelta >= iWarn:
        sResult = 'WARNING check_last_changed_ssh.py the {} file was modified {} days ago'.format(sMode, iDelta)
        iExitcode = 1
    elif iDelta < iWarn:
        sResult = 'OK check_last_changed_ssh.py the {} file was modified {} days ago'.format(sMode, iDelta)
        iExitcode = 0
    else:
        sResult = 'UNKNOWN'
        iExitcode = 3
    
    print(sResult)
    exit(iExitcode)    
    
def main():
    iDefaultWarn = 7
    iDefaultCrit = 14
    parser = argparse.ArgumentParser(description='Checks last change dates')
    parser.add_argument('-u', '--username', type=str, required=True, help="ssh username")
    parser.add_argument('-H', '--hostname', type=str, required=True, help="hostname")
    parser.add_argument('-P', '--path', type=str, required=True, help="path to check")
    parser.add_argument('-w', '--warn', type=int, default=iDefaultWarn, help="WARNING when file older then n days, default {}".format(iDefaultWarn))
    parser.add_argument('-c', '--crit', type=int, default=iDefaultCrit, help="CRITICAL when file older then n days, default {}".format(iDefaultCrit))
    parser.add_argument('-m', '--mode', type=str, default='youngest', help="judge oldest or youngest date (oldest|youngest)")
    parser.add_argument('-r', '--recursive', type=str, default='true', help="recursively check folders")
    parser.add_argument('-b', '--bsd', type=str, default='false', help="check if using BSD")
    args = parser.parse_args()
    
    bRecursive = True if args.recursive == 'true' else False
    bBSD = True if args.bsd == 'true' else False
    lDates = check(sUsername=args.username, sHostname=args.hostname, sPath=args.path, bRecursive=bRecursive, bBSD=bBSD)
    assert type(lDates) is list, 'lDates has to be of type list'
    for i, sDate in enumerate(lDates):
        assert type(sDate) is str, 'Dates in lDates have to be of type string'
        if sDate == '':
            lDates.pop(i)
    iDelta = parse(lDates=lDates, sMode=args.mode)
    assert type(iDelta) is int, 'iDelta hast to be of type int'
    printResult(iDelta=iDelta, iWarn=args.warn, iCrit=args.crit, sMode=args.mode)
    
if __name__ == "__main__":
    main()
