#!/usr/bin/python3
# check_drives_storcli.py - Python script that checks drive health
# intended for storcli
# for nagios style monitoring systems
#
# copyright C-Store 2015
# Author Mattis Haase
#
# usage:        check_drives_storcli.py warnErrors critErrors warnDown critDown
# output: OK/WARNING/CRITICAL check_srives_storecli - d0: 1/0, d0errors:0, .... dn: 1/0, dnerrors:0 | d0:1/0,d0errors:n,... 

from subprocess import check_output
import sys

storcliOutput = check_output(["/opt/lsi/storcli/storcli", "/c0", "/eall", "/sall", "show", "all"])
drives = []
warnErrors = sys.argv[1]
critErrors = sys.argv[2]
warnDown = sys.argv[3]
critDown = sys.argv[4]

i = -1
storcliOutput = storcliOutput.split('\n')
for line in storcliOutput:
	if 'GB SAS' in line:
		driveID = 's' + str(line.split(':')[1][:1])
		drives.append({'id':driveID})
		i += 1
		if 'Onln' in line:
			drives[i]['state'] = '1'
		elif 'Offln' in line:
			drives[i]['state'] = '0'
	elif "Media Error Count" in line:
		mediaErrorCount = str(line.split('=')[1][1:])
		drives[i]['mediaErrorCount'] = mediaErrorCount
	elif "Other Error Count" in line:
		otherErrorCount = str(line.split('=')[1][1:])
		drives[i]['otherErrorCount'] = otherErrorCount
	elif "BBM Error Count" in line:
		BBMErrorCount = str(line.split('=')[1][1:])
		drives[i]['BBMErrorCount'] = BBMErrorCount
	elif "Drive Temperature" in line:
		driveTemperature = str(line.split('=')[1][2:4])
		drives[i]['driveTemperature'] = driveTemperature
	elif "Predictive Failure Count" in line:
		predictiveFailureCount = str(line.split('=')[1][1:])
		drives[i]['predictiveFailureCount'] = predictiveFailureCount
	elif "S.M.A.R.T alert flagged by drive" in line:
		smartFlag = str(line.split('=')[1][1:])
		drives[i]['smartFlag'] = smartFlag
	
output = ''
#perfdata = ''
totalErrors = 0
totalDown = 0
for drive in drives:
	totalErrors += int(drive['mediaErrorCount']) + int(drive['otherErrorCount']) + int(drive['BBMErrorCount'])
	if drive['smartFlag'] == 'Yes': totalErrors += 1
	if drive['state'] == '0':	totalDown += 1
	output += drive['id'] + '_State=' + drive['state'] + ' ' + drive['id'] + '_MediaErrorCount=' + drive['mediaErrorCount'] + ' ' + drive['id'] + '_OtherErrorCount=' + drive['otherErrorCount'] + ' ' + drive['id'] + '_BBMErrorCount=' + drive['BBMErrorCount'] + ' ' + drive['id'] + '_PredictiveFailureCount=' + drive['predictiveFailureCount'] + ' ' +drive['id'] + '_Temp=' + drive['driveTemperature'] + ' ' + drive['id'] + '_SMARTTrip=' + drive['smartFlag'] + ' '
	
	#perfdata += drive['id'] + '_State=' + drive['state'] + ' ' + drive['id'] + '_MediaErrorCount=' + drive['mediaErrorCount'] + ' ' + drive['id'] + '_OtherErrorCount=' + drive['otherErrorCount'] + ' ' + drive['id'] + '_BBMErrorCount=' + drive['BBMErrorCount'] + ' ' + drive['id'] + '_PredictiveFailureCount=' + drive['predictiveFailureCount'] + ' ' +drive['id'] + '_Temp=' + drive['driveTemperature'] + ' ' + drive['id'] + '_SMARTTrip=' + drive['smartFlag'] + ' '

if int(totalErrors) >= int(critErrors) or int(totalDown) >= int(critDown):
	print('CRITICAL check_drives_storcli - ' + output + '|' + output)
elif int(totalErrors) >= int(warnErrors) or int(totalDown) >= int(warnDown):
	print('WARNING check_drives_storcli - ' + output + '|' + output)
elif int(totalErrors) < int(warnErrors) and int(totalDown) < int(warnDown):
	print('OK check_drives_storcli - ' + output + '|' + output)
else:
	print('UNKNOWN check_drives_storcli - ' + output + '|' + output)
