#!/usr/bin/python3
"""
This check combines memory, load and disk checks.

This file is under Apache 2.0 License

Copyright C-Store 2016
Author Mattis Haase
"""

from operator import itemgetter
import argparse

import psutil

def test_int(*args):
    for arg in args:
        assert type(arg) is int, 'should be Type Int'

def test_float(*args):
    for arg in args:
        assert type(arg) is float, 'should be Type Float'

def test_int_or_float(*args):
    for arg in args:
        assert type(arg) is int or type(arg) is float, 'should be Type Int or Float'
    
def test_string(*args):
    for arg in args:
        assert type(arg) is str, 'should be Type String'

def check_status(iWarning, iCritical, value):
    """
    Checks if status is OK, WARNING or CRITICAL
    
    Gets:
        iWarning: Warning Threshold
        iCritical: Critical Threshold
        value: value to check against
        
    Returns:
        'OK'|'WARNING'|'CRITICAL'|'UNKNOWN'
    """
    
    test_int(iWarning, iCritical)
    test_int_or_float(value)
    
    if value > iCritical:
        return 'CRITICAL'
    elif value > iWarning:
        return 'WARNING'
    elif value < iWarning:
        return 'OK'
    else:
        return 'UNKNOWN'

def calculate_percent(dValues):
    """
    Calculates percentages of all values in a dict.
    
    Gets: 
        dValues: dict with float or int numbers
        
    Returns:
        dict with same keywords as in dValues, but percentages as values
    """
    dPercentages = {}
    summed       = 0.0
    # for some reason sum gives an error, so we sum manually
    for key, value in dValues.items():
        test_int_or_float(value)
        summed += value
    for key, value in dValues.items():
        test_int_or_float(value)
        dPercentages[key] = round(100*value/summed, 2)
    return(dPercentages)

def check_load_or_memory(iWarning, iCritical, sCommand):
    """
    This checks for CPU or memory %. If WARNING or CRITICAL, also outputs top
    five processes which are using most CPU/memory
    
    Gets:
        iWarning: Warning Threshold
        iCritical: Critical Threshold
        sCommand: cpu | memory
    
    Returns:
        check output including perfdata
    """
    
    test_int(iWarning, iCritical)
    test_string(sCommand)
    
    sOutput   = ''
    sPerfdata = ''
    
    if sCommand.lower() == 'memory':
        odValues = psutil.virtual_memory()._asdict()
        test_int_or_float(odValues['percent'])
        sOutput = check_status(iWarning, iCritical, odValues['percent'])
    if sCommand.lower() == 'cpu':
        # psutil.cpu_times_percent() returns 0.0 for all percentages on some
        # systems. cpu_times() seems to work everywhere. So we calculate 
        # percentages ourselves
        odValues = psutil.cpu_times()._asdict()
        odValues = calculate_percent(odValues)
        sOutput = check_status(iWarning, iCritical, 100 - odValues['idle'])
    
    for key, value in odValues.items():
        if sPerfdata: sPerfdata += ' '
        sPerfdata += '{}={}'.format(key, value)
    
    # If WARNING or CRITICAL, we add the top memory consuming processes to output
    if sOutput != 'OK':
        lProcs = []
        
        # this iterates over all procs, which is very fast
        for proc in psutil.process_iter():
            # adds memory_percent for command memory or cpu_percent for command
            # cpu
            lProcs.append(proc.as_dict(attrs=['username', 'pid', 'name', sCommand.lower() + '_percent']))
        
        # sorting by either memory_percent or cpu_percent
        lProcs = sorted(lProcs, key = itemgetter(sCommand.lower() + '_percent'))
        
        # first line is header
        sProcs = 'Username, PID, Program, {}_Percent\n'.format(sCommand)
        
        # highest five processes get added to output
        for dProc in lProcs[0:5]:
            test_string(dProc['name'])
            test_int(dProc['pid'])
            test_int_or_float(dProc[sCommand.lower() + '_percent'])
            
            sProcs += '{}, {}, {}, {}\n'.format(
              dProc['username'],
              dProc['pid'],
              dProc['name'],
              dProc[sCommand.lower() + '_percent']
            )
        
        sOutput += ' over {} percent used. Top five consuming processes:\n\n {}'.format(iWarning, sProcs)
        
    # adding performance data and done
    sOutput += ' | {}'.format(sPerfdata)
    
    return sOutput

def main():
    parser = argparse.ArgumentParser(description='This check combines memory, load and disk checks.')
    parser.add_argument(
        '-w',
        '--warn',
        help='integer Percentage of RAM/CPU/Disk usage that leads to WARNING state. Default 85.',
        default = 85,
        type = int
    )
    parser.add_argument(
        '-c',
        '--crit',
        help='integer Percentage of RAM/CPU/Disk usage that leads to CRITICAL state. Default 95.',
        default = 95,
        type = int
    )
    parser.add_argument(
        '-C',
        '--command',
        help='<disk|cpu|memory>',
        default = 'memory',
        type = str
    )
    parser.add_argument(
        '-p',
        '--partition',
        help='partition that should trigger WARNING and CRITICAL states',
        default = '/',
        type = str
    )
    arguments = parser.parse_args()
    if arguments.command == 'cpu' or arguments.command == 'memory':
        print(check_load_or_memory(arguments.warn, arguments.crit, arguments.command))
if __name__ == '__main__':
    main()
