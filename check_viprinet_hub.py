#!/usr/bin/python

# check_viprinet_hub.py v0.1.0
# checks a Viprinet master hub for basic health information

# author	Dan Walker <dan@danwalker.com>
# created	2015-10-08

import argparse
import sys, os
import commands

# exit - exits execution with a state type and message
def exit(exit_code, message):
	exit_states = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']
	print exit_states[exit_code] + ': ' + message
	sys.exit(exit_code)

# the program
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-H', '--hostname', help = 'Remote host to query', required = True)
	parser.add_argument('-c', '--community', help = 'SNMP community (only v2c supported)', required = True)
	parser.add_argument('-t', '--type', help = 'Type of check to do (serial/tunnels/cpu/memory/temperature/power/fans)', required = True)
	
	parser.add_argument('-m', '--min', help = 'Minimum value (dependent on type supplied)', required = False)
	parser.add_argument('-M', '--max', help = 'Maximum value (dependent on type supplied)', required = False)
	
	parser.add_argument('-s', '--serial', help = 'Expected serial number', required = False)

	parser.add_argument('-D', '--debug', help = 'Show debugging info', required = False, action='store_true')

	parser.add_argument('-T', '--timeout', help = 'Time out for SNMP', default = '10', required = False)
	
	global args
	args = parser.parse_args()
	
	# default is to exit with an OK status
	exitCode = 0
	
	# tunnel check
	if args.type == 'tunnels':
		tunnels = snmpGetSingle('.1.3.6.1.4.1.35424.1.5.1')
		
		if args.min:
			if tunnels <= args.min:
				exitCode = 2
				
		if args.max:
			if tunnels >= args.max:
				exitCode = 2
		
		exit(exitCode, "Tunnels: " + tunnels + " |tunnels=" + tunnels)
		
	# serial check
	elif args.type == 'serial':
		serial = snmpGetSingle('.1.3.6.1.4.1.35424.1.1.2')
		
		if args.serial == serial:
			exit(0, "Correct serial identified (" + serial + ")")
		else:
			exit(2, "Incorrect serial identified (" + serial + ")")
	
	# cpu check
	elif args.type == 'cpu':
		load = snmpGetSingle('.1.3.6.1.4.1.35424.1.2.1.0')
		
		if args.max:
			if load >= args.max:
				exitCode = 2 
		
		exit(exitCode, 'Average CPU Load: ' + load + '%|cpu_load_average=' + load)
			 	
	# memory check
	elif args.type == 'memory':
		memUsage = snmpGetSingle('.1.3.6.1.4.1.35424.1.2.2.0')
		memUsage = str(int(memUsage) / 1000) # KB to MB

		if args.max:
			if memUsage >= args.max:
				exitCode = 2 
		
		exit(exitCode, 'Memory Usage Load: ' + memUsage + 'MB|memory_usage=' + memUsage)
		
	# temperature check
	elif args.type == 'temperature':
		temperature = snmpGetSingle('.1.3.6.1.4.1.35424.1.2.3.0')
		
		if args.max:
			if temperature >= args.max:
				exitCode = 2 
				
		exit(exitCode, 'Temperature: ' + temperature + 'C|temperature=' + temperature)
		
	# power check
	elif args.type == 'power':
		power = snmpGetSingle('.1.3.6.1.4.1.35424.1.2.5.0')
		
		if power != '0':
			exit(2, 'PSU fault detected')
			
		exit(exitCode, 'No PSU faults detected')
		
	# fan check
	elif args.type == 'fan':
		fans = snmpGetMultiple('.1.3.6.1.4.1.35424.1.3.2.1.1')
				
		output = ''
		perfData = ''
		
		for fan in fans:
			fanAdminStatus 	= snmpGetSingle('.1.3.6.1.4.1.35424.1.3.2.1.2.' + fan)
			fanOperStatus 	= snmpGetSingle('.1.3.6.1.4.1.35424.1.3.2.1.3.' + fan)
			fanRPM 			= snmpGetSingle('.1.3.6.1.4.1.35424.1.3.2.1.4.' + fan)
		
			if fanAdminStatus != '1':
				# fan not enabled
				exitCode = 2
				output += 'Fan ' + fan + ' is disabled, '
			elif fanOperStatus != '1':
				# fan not OK
				exitCode = 2
				output += 'Fan ' + fan + ' is not OK, '
			elif args.min and int(fanRPM) < int(args.min):
				# fan too slow
				exitCode = 1
				output += 'Fan ' + fan + ' RPM is ' + fanRPM + ', '
				
			# get fan speed regardless of whether we're alerting on it
			perfData += 'fan' + fan + '_speed=' + fanRPM + ' '
				
		if output == '':
			output = 'No fan faults detected'
		else:
			output = output[:-2]
			
		exit(exitCode, output + ' |' + perfData)

	# the type if statements didn't trigger, bad type likely 
	exit(3, 'Something went wrong')

def snmpGetSingle(oid):
	global args
	debug('Fetching OID: ' + oid)
	
	cmd = "snmpwalk -v2c -c " + args.community + " " + args.hostname + " -t " + args.timeout + " -On " + oid
	(status,output) = commands.getstatusoutput(cmd)
	
	value = output[output.rfind(":")+1:].strip()

	if value == 'noAccess':
		exit(2, 'Incorrect SNMP community')
	
	if value == ('No Response from ' + args.hostname):
		exit(2, 'No response from ' + args.hostname)

	# remove double quotes
	if value[0] == "\"":
		value = value[1:]
	
	if value[-1] == "\"":
		value = value[:-1]
	
	return value
	
def snmpGetMultiple(oid):
	global args
	debug('Fetching OID: ' + oid)
	cmd = "snmpwalk -v2c -c " + args.community + " " + args.hostname + " -t " + args.timeout + " -On " + oid
	(status,output) = commands.getstatusoutput(cmd)

	value = output[output.rfind(":")+1:].strip()

        if value == 'noAccess':
                exit(2, 'Incorrect SNMP community')

        if value == ('No Response from ' + args.hostname):
                exit(2, 'No response from ' + args.hostname)
	
	# split in to list
	output = output.splitlines()
	lines = []
	
	for line in output:
		debug('Dealing with line: ' + line)
		line = line[line.rfind(":")+1:].strip()
		
		if line != "":	
			# remove double quotes
			if line[0] == "\"":
				line = line[1:]
	
			if line[-1] == "\"":
				line = line[:-1]
			
		lines.append(line)
	
	return lines
	
def debug(message):
	if args.debug:
		print 'Debug: ' + str(message)
		
# actual program - just call the main function
main()