#!/usr/bin/python3
# check_smb.py - Python script that checks number of logged in SMB users
#
# copyright C-Store 2016
# Author Mattis Haase
#

import argparse, sys, os
import re
from sys import exit

import lib.sshcommand

def check(username, hostname):
    SSH = lib.sshcommand.SSHCommand()
    command = ['smbstatus', '-b']
    
    output = SSH.get(user = username, hostname = hostname, command = command)
    return output

def parse_output(output):
    ipv4_regex      = re.compile('\b(? :[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    ipv6_regex      = re.compile('(?<![:.\w])(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}(?![:.\w])')
    number_of_users = {}
    for entry in l_output[3:]:
        entry_elements = entry.split()
        address = re.search(ipv4_regex, entry_elements[4])
        if not address:
            address = re.search(ipv6_regex, entry_elements[4])
        address = address.group(0)
        if not address in number_of_users:
            number_of_users[address] = 1
        else:
            number_of_users[address] += 1
    return number_of_users

def print_result(number_of_users):
    output = 'OK - check_smb | {}'
    perfdata = ''
    total_users = 0
    for address, usercount in number_of_users.iteritems():
        total_users += usercount
        perfdata += ' {}={}'.format(address, usercount)
    perfdata +=' total_users={}'.format(total_users)
    output = output.format(perfdata)
    print(output)
    exit(0)

def main():
    parser = argparse.ArgumentParser(description='Checks number of logged in users')
    parser.add_argument('-u', '--username', type=str, required=True, help="ssh username")
    parser.add_argument('-H', '--hostname', type=str, required=True, help="hostname")
    args = parser.parse_args()
    
    username        = args.username
    hostname        = args.hostname
    output          = check(username, hostname)
    number_of_users = parse_output(output)
    
    print_result(number_of_users)
    
if __name__ == "__main__":
    main()
