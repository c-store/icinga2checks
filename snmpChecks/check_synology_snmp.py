#!/usr/bin/python3
# check_synology_snmp.py - Python script that checks synology Rackstations
#
# copyright C-Store 2015
# Author Mattis Haase
#
# usage: python check_synology_snmp.py user passwd command ip warn crit
# available commands:     system - returns system information, OK if system online, else critical. warn and crit can be set for temperature
#                        disk - returns disk information, warn and crit can be set for number of failed or crashed disks, else ok
#                        raid - returns raid information, will always warn on degraded, crit on crashed
#
# output: OK/WARNING/CRITICAL check_synology_snmp -

from sys import argv
from sys import exit
import argparse
from subprocess import check_output
from collections import OrderedDict

tree= {
    'synology':{
        'system':'.1.3.6.1.4.1.6574.1',
        'disk':'.1.3.6.1.4.1.6574.2',
        'raid':'.1.3.6.1.4.1.6574.3',
        'storage':'.1.3.6.1.2.1.25.2',
        'load':'.1.3.6.1.4.1.2021',
        'memory':'.1.3.6.1.4.1.2021.4'
    },
    'system':{
        'systemStatus':'1.0',
        'temperature':'2.0',
        'powerStatus':'3.0',
        'systemFanStatus':'4.1.0',
        'cpuFanStatus':'4.2.0',
        'modelName':'5.1.0',
        'serialNumber':'5.2.0',
        'version':'5.3.0',
        'upgradeAvailable':'5.4.0'
    },
    'disk':{
        'diskID':'1.1.2',
        'diskModel':'1.1.3',
        'diskStatus':'1.1.5',
        'diskTemp':'1.1.6'
    },
    'raid':{
        'name':'1.1.2',
        'raidStatus':'1.1.3'
    },
    'storage':{
        'name':'3.1.3',
        'totalSize':'3.1.5',
        'sizeUsed':'3.1.6'
    },
    'load':{
        'user':'11.9.0',
        'system':'11.10.0',
        'idle':'11.11.0',
        '1mload':'10.1.5.1',
        '5mload':'10.1.5.2',
        '15mload':'10.1.5.3'
    },
    'memory':{
        'memTotalSwap':'3.0',
        'memAvailSwap':'4.0',
        'memTotalReal':'5.0',
        'memAvailReal':'6.0', 
        'memTotalFree':'11.0', 
        'memShared':'13.0',
        'memBuffer':'14.0',
        'memCached':'15.0'
    }
}

returnCodes = {
    'raidStatus':{
        '1':'Normal',
        '2':'Repairing',
        '3':'Migrating',
        '4':'Expanding',
        '5':'Deleting',
        '6':'Creating',
        '7':'RaidSyncing',
        '8':'RaidParityChecking',
        '9':'RaidAssembling',
        '10':'Canceling',
        '11':'Degraded',
        '12':'Crashed'
    },
    'diskStatus':{
        '1':'Normal',
        '2':'Initialized',
        '3':'Not Initialized',
        '4':'SystemPartitionFailed',
        '5':'Crashed'
    },
    'upgradeAvailable':{
        '1':'Available',
        '2':'Unavailable',
        '3':'Connecting',
        '4':'Disconnected',
        '5':'Other'
    }
}

# gets: property in format synology.system.temperature
# returns: oid, for example: .1.3.6.1.4.1.6574.1.2.0
def getOID(property):
    assert (len(property.split('.')) == 2), 'property is supposed to have 2 elements'
    leaves = property.split('.')
    return tree[leaves[0]][leaves[1]]

def performCheck(oid, user, passwd, ip):
    output = check_output(['snmpwalk', '-v', '3', '-l', 'authNoPriv', '-u', user, '-A', passwd, ip, oid])
    return output.decode('utf-8').split('\n')

# gets: output of snmpwalk
#       property in format: synology.system
# returns: dict of format {systemStatus:1,temperature:40,...}
def mapOutput(output, property):
    leaves = property.split('.')
    d = OrderedDict()
    for line in output:
        if line != '' and line != '""':
            line = line.replace(' ', '').split('=')
            if line[1] != '' and line[1] != '""':
                line[0] = line[0].replace('iso', '.1')
                line[1] = line[1].split(':')[1]
                for key, element in tree[leaves[1]].items():
                    oid = tree[leaves[0]][leaves[1]] + '.' + element
                    newKey = ''
                    flag = False
                    #if its oid. then there are multiple properties
                    #(like multiple disks). so newkey = disk.status.id
                    if oid + '.' in line[0]:
                        newKey = leaves[1] + '.' + key + '.' + line[0][-1:]
                        flag = True
                    #if its just oid then there is only one property
                    #so newkey = disk.status
                    elif oid in line[0]:
                        newKey = leaves[1] + '.' + key
                        flag = True
                    if flag == True:
                        if key in returnCodes:
                            d[newKey] = returnCodes[key][line[1]]
                        else:
                            d[newKey] = line[1]
                        flag = False
    return d

# gets: mappedOutput
#       format: storage.name.0 = 'disk0'
#               storage.size.0 = 1234
# returns: mapped output, named
#       format: disk0.size = 1234
def rename(mappedOutput):
    names = {}
    for property, value in mappedOutput.items():
        # store the names and remove them
        if 'name' in property:
            # get the name of the sensor and remove the 'Temp'
            names[property.split('.')[2]] = value.replace('"','')
            mappedOutput.pop(property, None)
    for property, value in mappedOutput.items():
        leaves = property.split('.')
        if len(leaves) == 3:
            # = [temperatures, tempStatus, 2]
            newName = '{}.{}'.format(names[leaves[2]], leaves[1])
            mappedOutput[newName] = mappedOutput.pop(property)
    return(mappedOutput, names)

def checkSystem(oid, output, user, passwd, ip, warn, crit):
    if warn is None:
        warn = 50
    if crit is None:
        crit = 60
    status = ''
    sNonPerfdata = ''
    mappedOutput = mapOutput(output, 'synology.system')

    if int(mappedOutput['system.temperature']) >= crit or int(mappedOutput['system.systemStatus']) == 0 or int(mappedOutput['system.powerStatus']) == 0:
        status = 'CRITICAL '
    elif int(mappedOutput['system.temperature']) >= warn:
        status = 'WARNING '
    elif int(mappedOutput['system.temperature']) < warn:
        status = 'OK '
    else:
        status = 'UNKNOWN'
        
    for property, value in mappedOutput.items():
        if not 'temperature' in property:
            if value != '1':
                if value == '0': value = 'FAILURE'
                property = property.replace('system.', '')
                sNonPerfdata += '\n{}={}'.format(property, value)
            mappedOutput.pop(property, None)
            
    status += ' check_synology_snmp.py system - ' + sNonPerfdata
    status = status.replace('"', '')
    return [status, mappedOutput]

def checkRaid(oid, output, user, passwd, ip, warn, crit):
    if warn is None:
        warn = 1
    if crit is None:
        crit = 2
    status = ''
    mappedOutput = mapOutput(output, 'synology.raid')

    for property, value in mappedOutput.items():
        if 'raidStatus' in property:
            if value == 'Degraded':
                status = 'WARNING'
            elif value == 'Crashed':
                status = 'CRITICAL'
            elif value == 'Normal':
                status = 'OK'
            else:
                status = 'UNKNOWN'
    status +=' check_synology_snmp.py raid'
    for property, value in mappedOutput.items():
        if not 'Status' in property and value != 'Normal':
            status += '\n{} is {}'.format(property, value)
        mappedOutput.pop(property, None)
    status = status.replace('"', '')
    return [status, mappedOutput]

def checkDisk(oid, output, user, passwd, ip, warn, crit):
    if warn is None:
        warn = 1
    if crit is None:
        crit = 2
    status = ''
    dNames = {}
    mappedOutput = mapOutput(output, 'synology.disk')
    crashedDisks = 0
    damagedDisks = 0

    for property, value in mappedOutput.items():
        if 'diskStatus' in property:
            if value == 'SystemPartitionFailed':
                damagedDisks += 1
            elif value == 'Crashed':
                crashedDisks += 1
            else:
                #only failed drives need to show up in the output
                mappedOutput.pop(property, None)
        if 'ID' in property:
            #collect names of disks so IDs can later be replaced
            l = property.split('.')
            dNames[l[2]] = value
            mappedOutput.pop(property, None)

    if crashedDisks >= crit or damagedDisks >= crit:
        status = 'CRITICAL - the following disks have failed'
    elif crashedDisks >= warn or damagedDisks >= warn:
        status = 'WARNING - the following disks have failed'
    elif crashedDisks < warn and damagedDisks < warn:
        status = 'OK '
    else:
        status = 'UNKNOWN'
    
    for property, value in mappedOutput.items():
        if 'Status' in property:
            l = property.split('.')
            property = '{}.{}'.format(dNames[l[2]], l[1])
            status += '\n\n{} is {}'.format(property, value)
            mappedOutput.pop(property, None)
    for property, value in mappedOutput.items():
        if not 'Temp' in property:
            # replace 'disk.' with name and get rid of ID
            l = property.split('.')
            property = '{}.{}'.format(dNames[l[2]], l[1])
            status += '\n{}={}'.format(property, value)
            mappedOutput.pop(property, None)
    status = status.replace('"', '')
    return [status, mappedOutput]

def checkMemory(oid, output, user, passwd, ip, warn, crit):
    if warn is None:
        warn = 90
    if crit is None:
        crit = 99
    mappedOutput = mapOutput(output, 'synology.memory')
    dValues = {
        'maxSwap':int(mappedOutput['memory.memTotalSwap']),
        'freeSwap':int(mappedOutput['memory.memAvailSwap']),
        'maxRam':int(mappedOutput['memory.memTotalReal']),
        'freeRam':int(mappedOutput['memory.memAvailReal']), 
        'freeRamAndSwap':int(mappedOutput['memory.memTotalFree']), #including swap
        'shared':int(mappedOutput['memory.memShared']),
        'buffer':int(mappedOutput['memory.memBuffer']),
        'cached':int(mappedOutput['memory.memCached']),
    }
    dValues['maxRamAndSwap'] = dValues['maxRam'] + dValues['maxSwap']
    dValues['usedRam'] = dValues['maxRam'] - dValues['freeRam']
    dValues['usedSwap'] = dValues['maxSwap'] - dValues['freeSwap']
    dValues['usedRamNoBuffers'] = dValues['usedRam'] - dValues['buffer']
    dValues['usedRamPct'] = round(100 * dValues['usedRam'] / dValues['maxRam'], 1)
    dValues['usedSwapPct'] = round(100 * dValues['usedSwap'] / dValues['maxSwap'], 1)
    dValues['usedRamNoBuffersPct'] = round(100 * dValues['usedRamNoBuffers'] / dValues['maxRam'], 1)
    dValues['usedRamAndSwapNoBuffersPct'] = round(100 * (dValues['usedRamNoBuffers'] + dValues['usedSwap']) / dValues['maxRamAndSwap'], 1)
    
    if dValues['usedRamAndSwapNoBuffersPct'] < warn:
        status = 'OK check_synology_snmp.py memory'
    elif dValues['usedRamAndSwapNoBuffersPct'] < crit:
        status = 'WARNING check_synology_snmp.py memory - Used RAM is above {}%'.format(warn)
    elif dValues['usedRamAndSwapNoBuffersPct'] >= crit:
        status = 'CRITICAL check_synology_snmp.py memory - Used RAM is above {}%'.format(crit)
    else:
        status = 'UNKNOWN'

    return [status, dValues]

def checkLoad(oid, output, user, passwd, ip, warn, crit):
    if warn is None:
        warn = 90
    if crit is None:
        crit = 99
    mappedOutput = mapOutput(output, 'synology.load')
    
    if int(mappedOutput['load.5mload']) < warn:
        status = 'OK check_synology_snmp.py load'
    elif int(mappedOutput['load.5mload']) < crit:
        status = 'WARNING check_synology_snmp.py load - Used CPU is above {}%'.format(warn)
    elif int(mappedOutput['load.5mload']) >= crit:
        status = 'CRITICAL check_synology_snmp.py load - Used CPU is above {}%'.format(crit)
    else:
        status = 'UNKNOWN'

    return [status, mappedOutput]
    
def checkStorage(oid, output, user, passwd, ip, warn, crit):
    if warn is None:
        warn = 80
    if crit is None:
        crit = 90
    bCrit = False
    bWarn = False
    bOK   = False
    sWarnName = ''
    dValues = mapOutput(output, 'synology.storage')
    dValues, dNames = rename(dValues)
    
    #three properties per volume means there are dValues/3 volumes
    for i, sName in dNames.items():
        fUsedPct = round(100 * int(dValues[sName + '.sizeUsed']) / float(dValues[sName + '.totalSize']), 1)
        dValues[sName + '.usedPct'] = fUsedPct
        if 'volume' in sName:
            if fUsedPct >= crit: 
                bCrit = True
                bOK = False
                bWarn = False
                sWarnName = sName
            elif fUsedPct >= warn and fUsedPct < crit and not bCrit: 
                bWarn = True
                bOK = False
                sWarnName = sName
            elif fUsedPct < warn and not bWarn and not bCrit:
                bOK = True
            
    if bOK:
        status = 'OK check_synology_snmp.py storage'
    elif bWarn:
        status = 'WARNING check_synology_snmp.py storage - {} is filled {}%'.format(sWarnName, dValues[sWarnName + '.usedPct'])
    elif bCrit:
        status = 'CRITICAL check_synology_snmp.py storage - {} is filled {}%'.format(sWarnName, dValues[sWarnName + '.usedPct'])
    else:
        status = 'UNKNOWN'

    return [status, dValues]

def buildOutput(status, mappedOutput, command):
    properties = ''
    for property, value in mappedOutput.items():
        properties += ' ' + property + '=' + str(value)
    outputString = '{}|{}'.format(status, properties)
    return outputString

def main():
    status    = 'unknown'
    mappedOutput = {}

    parser = argparse.ArgumentParser(description='Synology RackStation SNMP based check.')
    parser.add_argument('-u', '--username', type=str, help="SNMPv3 username")
    parser.add_argument('-p', '--passwd', type=str, help="SNMPv3 auth password.")
    parser.add_argument('-C', '--command', type=str, help="Check to be executed. Can be system, disk, raid, memory, load or storage.")
    parser.add_argument('-H', '--host', type=str, help="Hostname or IP address")
    parser.add_argument('-w', '--warn', type=int, help="warnlevel")
    parser.add_argument('-c', '--crit', type=int, help="critlevel")
    args = parser.parse_args()

    user    = args.username
    passwd    = args.passwd
    command = args.command
    ip        = args.host
    warn    = args.warn
    crit    = args.crit
    
    if command == 'system':
        oid = getOID('synology.system')
        output = performCheck(oid, user, passwd, ip)
        status, mappedOutput = checkSystem(oid, output, user, passwd, ip, warn, crit)
    elif command == 'disk':
        oid = getOID('synology.disk')
        output = performCheck(oid, user, passwd, ip)
        status, mappedOutput = checkDisk(oid, output, user, passwd, ip, warn, crit)
    elif command == 'raid':
        oid = getOID('synology.raid')
        output = performCheck(oid, user, passwd, ip)
        status, mappedOutput = checkRaid(oid, output, user, passwd, ip, warn, crit)
    elif command == 'memory':
        oid = getOID('synology.memory')
        output = performCheck(oid, user, passwd, ip)
        status, mappedOutput = checkMemory(oid, output, user, passwd, ip, warn, crit)
    elif command == 'load':
        oid = getOID('synology.load')
        output = performCheck(oid, user, passwd, ip)
        status, mappedOutput = checkLoad(oid, output, user, passwd, ip, warn, crit)
    elif command == 'storage':
        oid = getOID('synology.storage')
        output = performCheck(oid, user, passwd, ip)
        status, mappedOutput = checkStorage(oid, output, user, passwd, ip, warn, crit)
    outputString = buildOutput(status, mappedOutput, command)
    print(outputString)
    if 'OK' in outputString: exit(0)
    elif 'WARNING' in outputString: exit(1)
    elif 'CRITICAL' in outputString: exit(2)
    elif 'UNKNOWN' in outputString: exit(3)

if __name__ == "__main__":
   main()
