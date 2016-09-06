#!/usr/bin/python3
# check_imm2.py - IMM2
# for nagios style monitoring systems
#
# this checks via SNMP v3
#
# copyright C-Store 2016
# Author Mattis Haase
import argparse
from sys import exit
from subprocess import check_output
from collections import OrderedDict

# define all oids
tree= {
    'ibm': {
        'fans': '1.3.6.1.4.1.2.3.51.3.1.3.2.1',
        'temperatures': '1.3.6.1.4.1.2.3.51.3.1.1.2.1',
        'voltages': '1.3.6.1.4.1.2.3.51.3.1.2.2.1',
        'sysinfos': '1.3.6.1.4.1.2.3.51.3.1.5.2.1',
        'disks': '1.3.6.1.4.1.2.3.51.3.1.13.1',
        'hwhealth': '1.3.6.1.4.1.2.3.51.3.1.4.1'
    },
    'fans': {
        'fanPercent':'3',
        'fanStatus':'10' #Normal/Critical
    },
    'temperatures': {
        'name':'2',
        'temp':'3',
        'tempNominal':'4',
        'crit':'6',
        'warn':'7',
        'status':'11' #Normal/Unknown/Critical
    },
    'voltages': {
        'name':'2',
        'voltage':'3',
        'voltageNominal':'4',
        'critLow':'9',
        'critHigh':'6',
        'status':'11' #Normal/Critical
    },
    'sysinfos': {
        'type':'1',
        'model':'2',
        'serial':'3',
        'uuid':'4',
    },
    'hwhealth': { 'hwStatus': '0' }, #HW status - 255 OK, 0 Crit, 2 Warn}
    'disks': {
        'controllerName': '2.1.3',
        'controllerSerial': '2.1.10',
        'controllerCache': '2.1.14',
        #'poolID': '2.1.37',
        #'poolAttachedDisks': '2.1.38',
        'disk_Name': '3.1.2',
        'disk_Model': '3.1.3',
        'disk_Status': '3.1.4', #Online/Unconfigured Bad/Unconfigured Good/JBOD
        'disk_Port': '3.1.5',
        'disk_AttachedType': '3.1.7', #SATA/SAS
        'disk_Type': '3.1.8', #HDD/SSD
        'disk_Bandwidth': '3.1.9',
        'disk_Temperature': '3.1.10',
        'disk_Size': '3.1.12',
        'disk_Serial': '3.1.17',
        #'storagePools': '6.1.2',
        'volumeRaidLevel': '6.1.4',
        #'volumeSize': '6.1.5',
        #'volumeName': '6.1.6',
        #'volumeMembers': '6.1.7',
        'volumeName': '7.1.2',
        'volumeStatus': '7.1.4' # Optimal/Degraded
    }
}

# gets: property in format synology.system.temperature
# returns: oid, for example: .1.3.6.1.4.1.6574.1.2.0
def getOID(property):
    assert (len(property.split('.')) == 2), 'property is supposed to have 2 elements'
    leaves = property.split('.')
    return tree[leaves[0]][leaves[1]]

def performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo):
    if level == "authPriv":
        output = check_output(['snmpwalk', '-v', '3', '-l', 'authPriv', '-u', user, '-a', authAlgo, '-A', authPasswd, '-x', privAlgo, '-X', privPasswd, ip, oid])
    elif level == 'authNoPriv':
        output = check_output(['snmpwalk', '-v', '3', '-l', 'authNoPriv', '-u', user, '-a', authAlgo, '-A', authPasswd, ip, oid])
    elif level == 'noAuthNoPriv':
        output = check_output(['snmpwalk', '-v', '3', '-l', 'noAuthNoPriv', '-u', user, ip, oid])
    return output.decode('utf-8').replace('"', '').split('\n')

# gets: output of snmpwalk
#       property in format: ibm.disks
# returns: dict of format {systemStatus:1,temperature:40,...}
def mapOutput(output, property):
    leaves = property.split('.')
    # return list of format ('ibm', 'disks')
    d = OrderedDict()
    for line in output:
        if ':' in line:
            # line of format iso.3.6.1.4.1.2.3.51.3.1.13.1.3.1.20.1 = STRING: "Drive"
            line = line.replace(' ', '').split('=')
            # return list of format ('iso.3.6.1.4.1.2.3.51.3.1.13.1.3.1.20.1', 'STRING:"Drive"')
            line[0] = line[0].replace('iso', '1')
            line[1] = line[1].split(':')[1]
            # return list of format ('1.3.6.1.4.1.2.3.51.3.1.13.1.3.1.20.1', '"Drive"')
            for key, element in tree[leaves[1]].items():
                # for element in disks oid = element
                oid = tree[leaves[0]][leaves[1]] + '.' + element
                # oid = tree[ibm][disks].element
                newKey = ''
                flag = False
                #if its oid.number then there are multiple properties
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
                    d[newKey] = line[1]
                    flag = False
    return d

def checkFans(output):
    warn = 1
    crit = 2
    status = ''
    mappedOutput = mapOutput(output, 'ibm.fans')
    criticalFans = 0
    failedFans = []
    for property, value in mappedOutput.items():
        if 'fanStatus' in property:
            # count offline fans
            if value == '"Critical"':
                criticalFans += 1
                # append failed fan id
                failedFans.append('fan{}'.format(property.split('.')[2]))
            # then remove from dict.
            mappedOutput.pop(property, None)
        # remove '% of maximum'
        if 'fanPercent' in property:
            if value != 'offline':
                mappedOutput[property] = mappedOutput[property][0:2]
            else:
                mappedOutput[property] = mappedOutput[property]
    for property, value in mappedOutput.items():
        propertyList = property.split('.')
        if len(propertyList) == 3:
            newname = 'fan{}.pct'.format(propertyList[2])
            mappedOutput[newname] = mappedOutput.pop(property)

    if criticalFans >= crit:
        status = 'CRITICAL failed fans: {}'.format(failedFans)
    elif criticalFans >= warn:
        status = 'WARNING failed fans: {}'.format(failedFans)
    elif criticalFans < warn:
        status = 'OK'
    else:
        status = 'UNKNOWN'
    return [status, mappedOutput]

def checkTemperatures(output):
    status = ''
    nonPerfdata = ''
    mappedOutput = mapOutput(output, 'ibm.temperatures')
    names = {}
    criticalTemps = []

    for property, value in mappedOutput.items():
        # store the names and remove them
        if 'name' in property:
            # get the name of the sensor and remove the 'Temp'
            names[property.split('.')[2]] = value[:-4]
            mappedOutput.pop(property, None)
    for property, value in mappedOutput.items():
        leaves = property.split('.')
        if len(leaves) == 3:
            # = [temperatures, tempStatus, 2]
            newName = '{}.{}'.format(names[leaves[2]], leaves[1])
            mappedOutput[newName] = mappedOutput.pop(property)
    for property, value in mappedOutput.items():
        # count critical temperaturs
        if 'status' in property:
            if value == 'Critical':
                criticalTemps.append(property)
                status = 'CRITICAL - following temperatures are critical: {}'.format(criticalTemps)
            mappedOutput.pop(property, None)
        if 'crit' in property or 'warn' in property:
            nonPerfdata += '\n{}={}'.format(property, mappedOutput[property])
            mappedOutput.pop(property, None)
    if not status == 'CRITICAL':
        status = 'OK'

    status += nonPerfdata
    return [status, mappedOutput]

def checkVoltages(output):
    status = ''
    nonPerfdata = ''
    mappedOutput = mapOutput(output, 'ibm.voltages')
    names = {}
    criticalTemps = []
    for property, value in mappedOutput.items():
        # store the names and remove them
        if 'name' in property:
            # get the name of the sensor and remove the 'Temp'
            names[property.split('.')[2]] = value
            mappedOutput.pop(property, None)
    for property, value in mappedOutput.items():
        leaves = property.split('.')
        if 'voltages' in leaves:
            # = [temperatures, tempStatus, 2]
            newName = '{}.{}'.format(names[leaves[2]], leaves[1])
            mappedOutput[newName] = mappedOutput.pop(property)
    for property, value in mappedOutput.items():
        # count critical temperaturs
        if 'status' in property:
            if value == 'Critical':
                criticalVoltages.append(property)
                status = 'CRITICAL - following voltages are critical: {}'.format(criticalVoltages)
            mappedOutput.pop(property, None)
        if 'crit' in property:
            nonPerfdata += '\n{}={}'.format(property, mappedOutput[property])
            mappedOutput.pop(property, None)
    if not status == 'CRITICAL':
        status = 'OK'
    status += nonPerfdata
    return [status, mappedOutput]

def checkSysinfos(output):
    status = 'OK'
    mappedOutput = mapOutput(output, 'ibm.sysinfos')
    for property, value in mappedOutput.items():
        propertyList = property.split('.')
        if len(propertyList) == 3:
            status += '\n{}={}'.format(propertyList[1], mappedOutput.pop(property))
    return [status, mappedOutput]

def checkHwhealth(output):
    status = ''
    mappedOutput = mapOutput(output, 'ibm.hwhealth')
    hwStatus = 0
    for property, value in mappedOutput.items():
        if 'hwStatus' in property:
            hwStatus = value
            mappedOutput.pop(property, None)
    if hwStatus == '0':
        status = 'CRITICAL'
    elif hwStatus == '2':
        status = 'WARNING'
    elif hwStatus == '255':
        status = 'OK'
    else:
        status = 'UNKNOWN'
    return [status, mappedOutput]

def checkDisks(output):
    status = ''
    nonPerfdata = ''
    type = ''
    names = { 'disk_':{}, 'controller':{}, 'volume':{}}
    mappedOutput = mapOutput(output, 'ibm.disks')
    numberDegraded = 0
    degradedVolumes = []
    for property, value in mappedOutput.items():
        if 'Name' in property:
            propertyList = property.split('.')
            if len(propertyList) == 3:
                type = propertyList[1][:-4]
                names[type][propertyList[2]] = value
            mappedOutput.pop(property, None)
    for property, value in mappedOutput.items():
        if 'controller' in property:
            type = 'controller'
        elif 'disk_' in property:
            type = 'disk_'
        elif 'volume' in property:
            type = 'volume'
        if type in ['controller', 'disk_', 'volume']:
            propertyList = property.split('.')
            if len(propertyList) == 3:
                newName = '{}.{}'.format(names[type][propertyList[2]], propertyList[1])
                if not 'Temperature' in property and not 'volumeStatus' in property:
                    nonPerfdata += '\n{}={}'.format(newName, mappedOutput[property])
                    mappedOutput.pop(property, None)
                elif 'Temperature' in property:
                    mappedOutput[newName] = mappedOutput.pop(property)[:-1]
                else:
                    mappedOutput[newName] = mappedOutput.pop(property)
    for property, value in mappedOutput.items():
        if 'volumeStatus' in property:
            if value == 'Degraded':
                numberDegraded += 1
                degradedVolumes.append(property.split('.')[0])
                mappedOutput.pop(property, None)
    if numberDegraded >= 1:
        status = 'CRITICAL - the following volumes are degraded: {} - '.format(degradedVolumes)
    else:
        status = 'OK'
    status += nonPerfdata
    return [status, mappedOutput]

def buildOutput(status, mappedOutput, command):
    outputString = status
    properties = ''
    perfdata = ''
    for property, value in mappedOutput.items():
        properties += ' ' + property + '=' + str(value)
        if type(value) == int:
            perfdata += ' ' + property + '=' + str(value)
    if properties:
        outputString += ' |' + properties
    return outputString

def main():
    status    = 'unknown'
    mappedOutput = {}

    parser = argparse.ArgumentParser(description='IBM IMM2 SNMP3 based check.')
    parser.add_argument('-u', '--username', type=str, help="set security name (e.g. bert)")
    parser.add_argument('-a', '--authAlgo', type=str, help="set authentication protocol (MD5|SHA)")
    parser.add_argument('-A', '--authPasswd', type=str, help=" set authentication protocol pass phrase")
    parser.add_argument('-x', '--privAlgo', type=str, help="set privacy protocol (DES|AES)")
    parser.add_argument('-X', '--privPasswd', type=str, help="set privacy protocol pass phrase")
    parser.add_argument('-l', '--level', type=str, help="set security level (noAuthNoPriv|authNoPriv|authPriv)")
    parser.add_argument('-C', '--command', type=str, help="Check to be executed (fans|temperatures|voltages|sysinfos|disks|hwhealth)")
    parser.add_argument('-H', '--host', type=str, help="Hostname or IP address")

    args = parser.parse_args()

    user       = args.username
    command    = args.command
    ip         = args.host
    authAlgo   = args.authAlgo
    authPasswd = args.authPasswd
    privAlgo   = args.privAlgo
    privPasswd = args.privPasswd
    level      = args.level

    if command == 'fans':
        oid = getOID('ibm.fans')
        output = performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo)
        status, mappedOutput = checkFans(output)
    elif command == 'temperatures':
        oid = getOID('ibm.temperatures')
        output = performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo)
        status, mappedOutput = checkTemperatures(output)
    elif command == 'voltages':
        oid = getOID('ibm.voltages')
        output = performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo)
        status, mappedOutput = checkVoltages(output)
    elif command == 'sysinfos':
        oid = getOID('ibm.sysinfos')
        output = performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo)
        status, mappedOutput = checkSysinfos(output)
    elif command == 'disks':
        oid = getOID('ibm.disks')
        output = performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo)
        status, mappedOutput = checkDisks(output)
    elif command == 'hwhealth':
        oid = getOID('ibm.hwhealth')
        output = performCheck(oid, user, authPasswd, privPasswd, ip, level, authAlgo, privAlgo)
        status, mappedOutput = checkHwhealth(output)
    outputString = buildOutput(status, mappedOutput, command)
    print(outputString)
    if 'OK' in outputString: exit(0)
    elif 'WARNING' in outputString: exit(1)
    elif 'CRITICAL' in outputString: exit(2)
    elif 'UNKNOWN' in outputString: exit(3)

if __name__ == "__main__":
    main()

assert (getOID('ibm.disks') == '1.3.6.1.4.1.2.3.51.3.1.13.1'),'assert error, ibm.disks not parsed correctly'
