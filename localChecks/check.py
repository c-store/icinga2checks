#!/usr/bin/python3
"""
This check combines memory, load and disk checks.

This file is under Apache 2.0 License

Copyright C-Store 2016
Author Mattis Haase
"""

from operator import itemgetter

import psutil

def test_int(*args):
    for arg in args:
        assert_(type(arg) is IntType, 'should be Type Int')

def test_float(*args):
    for arg in args:
        assert_(type(arg) is FloatType, 'should be Type Float')

def test_int_or_float(*args):
    for arg in args:
        assert_(type(arg) is IntType or type(arg) is FloatType, 'should be Type Int or Float')
    
def test_string(*args):
    for arg in args:
        assert_(type(arg) is StringType, 'should be Type String')

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
    
def check_load_or_memory(iWarning, iCritical, sCommand):
    """
    This checks for CPU or memory %. If WARNING or CRITICAL, also outputs top
    five processes which are using CPU/memory
    
    Gets:
        iWarning: Warning Threshold
        iCritical: Critical Threshold
        sCommand: cpu | memory
    
    Returns:
        check output including perfdata
    """
    
    test_int(iWarning, iCritical)
    test_string(sCommand)
    
    if sCommand.lower() == 'memory':
        dValues   = psutil.virtualmemory()._asdict
        sOutput = check_status(iWarning, iCritical, dValues['percent'])
    if sCommand.lower() == 'cpu':
        dValues   = psutil.cpu_times_percent()._asdict
        sOutput = check_status(iWarning, iCritical, 100 - dValues['idle'])
    
    sPerfdata = ''
    sOutput   = ''
    
    for key, value in enumerate(dValues):
        if sPerfdata:
            sPerfdata += ' '
        sPerfdata += '{}={}'.format(key, value)
    
    # If WARNING or CRITICAL, we add the top memory consuming processes to output
    if sOutput != 'OK':
        lProcs = []
        
        # this iterates over all procs, which is very fast
        for proc in psutil.process_iter():
            lProcs.append(proc.as_dict(attrs=['username', 'pid', 'name', sCommand.lower() + '_percent']))
        
        # sorting by either memory_percent or cpu_percent
        lProcs = sorted(lProcs, key = itemgetter(sCommand.lower() + '_percent'))
        
        # first line is header
        sProcs = 'Username, PID, Program, {}_Percent\n'.format(sCommand)
        
        # highest five processes get added to output
        for dProc in lProcs[0:4]:
            test_string(dProc['username'], dProc['name'])
            test_int(dProc['pid'])
            test_int_or_float(dProc[sCommand.lower() + '_percent'])
            
            sProcs += '{}, {}, {}, {}, {}\n'.format(
              dProc['username'],
              dProc['pid'],
              dProc['name'],
              dProc[sCommand.lower() + '_percent']
            )
        
        sOutput += '\n\n {}'.format(sProcs)
        
    # adding performance data and done
    sOutput += ' | {}'.format(sPerfdata)
    
    return sOutput
