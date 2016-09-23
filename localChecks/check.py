#!/usr/bin/python3
"""
This check combines memory, load, disk and network checks.

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
        
def add_perfdata(s_perfdata, s_prefix, s_key, value):
    test_string(s_perfdata, s_prefix, s_key)
    test_int_or_float(value)
    
    if s_perfdata: s_perfdata += ' '
    s_perfdata += '{}.{}={}'.format(
        s_prefix,
        s_key,
        value
    )
    
    return s_perfdata

def check_status(i_warning, i_critical, value):
    """
    Checks if status is OK, WARNING or CRITICAL
    
    Gets:
        i_warning: Warning Threshold
        i_critical: Critical Threshold
        value: value to check against
        
    Returns:
        'OK'|'WARNING'|'CRITICAL'|'UNKNOWN'
    """
    
    test_int(i_warning, i_critical)
    test_int_or_float(value)
    
    if value > i_critical:
        return 'CRITICAL'
    elif value > i_warning:
        return 'WARNING'
    elif value < i_warning:
        return 'OK'
    else:
        return 'UNKNOWN'

def calculate_percent(d_values):
    """
    Calculates percentages of all values in a dict.
    
    Gets: 
        d_values: dict with float or int numbers
        
    Returns:
        dict with same keywords as in d_values, but percentages as values
    """
    d_percentages = {}
    summed       = 0.0
    # for some reason sum gives an error, so we sum manually
    for key, value in d_values.items():
        test_int_or_float(value)
        summed += value
    for key, value in d_values.items():
        test_int_or_float(value)
        d_percentages[key] = round(100*value/summed, 2)
    return(d_percentages)

def check_load_or_memory(i_warning, i_critical, s_command):
    """
    This checks for CPU or memory %. If WARNING or CRITICAL, also outputs top
    five processes which are using most CPU/memory
    
    Gets:
        i_warning: Warning Threshold
        i_critical: Critical Threshold
        s_command: cpu | memory
    
    Returns:
        check output including perfdata
    """
    
    test_int(i_warning, i_critical)
    test_string(s_command)
    
    s_output   = ''
    s_perfdata = ''
    
    if s_command.lower() == 'memory':
        od_values = psutil.virtual_memory()._asdict()
        test_int_or_float(od_values['percent'])
        s_output = check_status(i_warning, i_critical, od_values['percent'])
    if s_command.lower() == 'cpu':
        # psutil.cpu_times_percent() returns 0.0 for all percentages on some
        # systems. cpu_times() seems to work everywhere. So we calculate 
        # percentages ourselves
        od_values = psutil.cpu_times()._asdict()
        od_values = calculate_percent(od_values)
        s_output = check_status(i_warning, i_critical, 100 - od_values['idle'])
    
    for key, value in od_values.items():
        if s_perfdata: s_perfdata += ' '
        s_perfdata += '{}={}'.format(key, value)
    
    # If WARNING or CRITICAL, we add the top memory consuming processes to output
    if s_output != 'OK':
        l_procs = []
        
        # this iterates over all procs, which is very fast
        for proc in psutil.process_iter():
            # adds memory_percent for command memory or cpu_percent for command
            # cpu
            l_procs.append(proc.as_dict(attrs=['username', 'pid', 'name', s_command.lower() + '_percent']))
        
        # sorting by either memory_percent or cpu_percent
        l_procs = sorted(l_procs, key = itemgetter(s_command.lower() + '_percent'))
        
        # first line is header
        s_procs = 'Username, PID, Program, {}_Percent\n'.format(s_command)
        
        # highest five processes get added to output
        for d_proc in l_procs[0:5]:
            test_string(d_proc['name'])
            test_int(d_proc['pid'])
            test_int_or_float(d_proc[s_command.lower() + '_percent'])
            
            s_procs += '{}, {}, {}, {}\n'.format(
              d_proc['username'],
              d_proc['pid'],
              d_proc['name'],
              d_proc[s_command.lower() + '_percent']
            )
        
        s_output += ' over {} percent used. Top five consuming processes:\n\n {}'.format(i_warning, s_procs)
        
    # adding performance data and done
    s_output += ' | {}'.format(s_perfdata)
    
    return s_output

def check_disk(i_warning, i_critical, s_partition):
    """
    Checks for disk stats
    
    Gets:
        i_warning: Warning Threshold
        i_critical: Critical Threshold
        s_partition: partition that should be used to trigger WARNING/CRITICAL
    
    Returns:
        check output including perfdata
    """
    test_int(i_warning, i_critical)
    test_string(s_partition)
    
    s_perfdata                  = ''
    s_output                    = ''
    l_partitions                = psutil.disk_partitions()
    d_io_counters               = psutil.disk_io_counters(perdisk=True)
    f_monitored_partition_usage = 0.0
    
    for nt_partition in l_partitions:
        # get usage for every partition
        d_disk_usage = psutil.disk_usage(nt_partition.mountpoint)._asdict()
        # add all usage data to perfdata
        for key, value in d_disk_usage.items():
            s_perfdata = add_perfdata(s_perfdata, nt_partition.mountpoint, key, value)
        
        # check monitored partition and add status to output
        if nt_partition.mountpoint == s_partition:
            s_output = check_status(i_warning, i_critical, d_disk_usage['percent'])
            f_monitored_partition_usage = d_disk_usage['percent']
    
    # add message if status is not OK
    if not 'OK' in s_output:
        s_output += ' {} has a usage of {} percent.'.format(s_partition, f_monitored_partition_usage)
    
    # add all the mountpoints and other info to output
    for nt_partition in l_partitions:
        d_partition = nt_partition._asdict()
        for key, value in d_partition.items():
            if not key == 'device':
                s_output += '\n{}.{}={}'.format(
                    d_partition['device'],
                    key,
                    value
                )
    
    for s_device, nt_partition in d_io_counters.items():
        d_partition = nt_partition._asdict()
        # add all io_counters to perfdata
        for key, value in d_partition.items():
            s_perfdata = add_perfdata(s_perfdata, s_device, key, value)
    
    # put it all together
    s_output += ' | {}'.format(s_perfdata)
    
    return s_output

def check_network(i_warning, i_critical):
    test_int(i_warning, i_critical)
    
    s_perfdata    = ''
    s_output      = ''
    i_max         = 0
    s_maxdesc     = ''
    d_io_counters = psutil.net_io_counters(pernic=True)
    
    for s_device, nt_counters in d_io_counters.items():
        d_counters = nt_counters._asdict()
        # add all io_counters to perfdata
        for key, value in d_counters.items():
            if 'err' in key or 'drop' in key:
                if value > i_max: 
                    i_max = value
                    s_maxdesc = '{} has {} {} packets.'.format(s_device, value, key)
            s_perfdata = add_perfdata(s_perfdata, s_device, key, value)
            
    s_output = check_status(i_warning, i_critical, i_max)
    
    if not 'OK' in s_output: s_output += s_maxdesc
    
    s_output += ' | {}'.format(s_perfdata)
    
    return s_output

def main():
    parser = argparse.ArgumentParser(description='This check combines memory, load and disk checks.')
    parser.add_argument(
        '-w',
        '--warn',
        help='For cpu|memory|disk Percentage usage. For net number of dropped/error packets. Default 85',
        default = 85,
        type = int
    )
    parser.add_argument(
        '-c',
        '--crit',
        help='For cpu|memory|disk Percentage usage. For network number of dropped/error packets. Default 95',
        default = 95,
        type = int
    )
    parser.add_argument(
        '-C',
        '--command',
        help='<disk|cpu|memory|network> Default memory.',
        default = 'memory',
        type = str
    )
    parser.add_argument(
        '-p',
        '--partition',
        help='partition that should trigger WARNING and CRITICAL states. Default /',
        default = '/',
        type = str
    )
    arguments = parser.parse_args()
    if arguments.command == 'cpu' or arguments.command == 'memory':
        print(check_load_or_memory(arguments.warn, arguments.crit, arguments.command))
    if arguments.command == 'disk':
        print(check_disk(arguments.warn, arguments.crit, arguments.partition))
    if arguments.command == 'network':
        print(check_network(arguments.warn, arguments.crit))
if __name__ == '__main__':
    main()
