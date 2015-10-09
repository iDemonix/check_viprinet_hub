# check_viprinet_hub

This Nagios/Icinga plugin checks various health aspects of a Viprinet Hub including serial number (for failover checking), tunnel count, average CPU, memory usage, PSU faults and fan status.

The check works by wrapping the *snmpwalk* command, which is a requirement. A Python SNMP library is not used due to the high availability of *snmpwalk* in the production environment I developed this for. The script also only supports the v2c implementation of SNMP, although v3 support could be added if anyone needs it. Currently only supports standard SNMP port too, I can add an argument if the demand exists.

Output also makes use of perfdata where appropriate.

## Example Usage

	[dwalker@dan01 ~]$ python check_viprinet_hub.py -H 10.0.0.1 -c public -t fan 
	OK: No fan faults detected |fan1_speed=2592 fan2_speed=2580 
	
	[dwalker@dan01 ~]$ python check_viprinet_hub.py -H 10.0.0.1 -c public -t tunnels
	OK: Tunnels: 118 |tunnels=118
	
	[dwalker@dan01 ~]$ python check_viprinet_hub.py -H 10.0.0.1 -c public -t tunnels -m 10 -M 100
	CRITICAL: Tunnels: 118 |tunnels=118
	
	[dwalker@dan01 ~]$ python check_viprinet_hub.py -H 10.0.0.1 -c public -t temperature         
	OK: Temperature: 27C|temperature=27
	
	[dwalker@dan01 ~]$ python check_viprinet_hub.py -H 10.0.0.1 -c public -t cpu        
	OK: Average CPU Load: 26%|cpu_load_average=26
	
## Arguments

	-H --hostname 			Address of the Viprinet Hub to check
	-c --community			SNMP community (v2c)
	-t --type			Type of check (serial/tunnels/cpu/memory/temperature/power/fans)
	-m --min			Minimum (used by tunnels and fan RPM)
	-M --max			Maximum (used by tunnels, cpu, memory, temperature)
	-s --serial			Required if checking type 'serial' (simple check for failover)
	-D 				Debug mode
	-T --timeout			Timeout passed to snmpwalk

## Issues and Requests

If anyone finds a bug or would like to request a new feature, please do so via GitHub.
