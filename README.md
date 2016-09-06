# icinga2checks
Aiming to make standard checks more useful

These are a variety of python based icinga2 checks that either did not exist yet or that add some functionality to existing checks.

The biggest design goal for these checks is that they have to be actually useful in a real world scenario. This means that the check output does not contain useless information - things that should only be performance data are performance data, and things that should only be in the check output (like serial numbers), are only in the check output. The plugins also take advantage of the revolutionary new technology called newline, making output more readable.

Some plugins also perform differently in OK, WARNING or CRITICAL conditions. check_mem.py for example returns the most memory consuming processes in WARNING or CRITICAL.

All python checks use the python parser module, which provides command line help.

We aim to also have a consistent coding style and good documentation within the code. This is of course work in progress.

## checks at this time
Checks are divided into local checks, which have to be present on the client, remote checks, which only have to be present on the server, and snmp checks, which utilize snmp. Checks with an asterisk are legacy checks that do not yet comply to our documentation standards.

### Local checks

**check_disk.py** - Lists all partitions with mountpoints, performance data includes blocks used, blocks total, blocks free and percent used. Allows to set critical/warning percent on specific partition.

**check_mem.py** - Output consists of OK when OK, first two lines of ps sorted by memory utilization if warning or critical. Performance data includes all the information given by the unix free -m command.

**check_drives_storcli.py*** - Lists up/down status and error count of all volumes and drives. Warning/Critical based on error count and number of offline drives.

**check_drives_load.sh*** - Lists number of cores, 1, 5 and 15 min loads. Performance data includes load percent calculated as load * 100 / cores.

### Remote checks

**check_last_changed_ssh.py** - Checks age of files in remote folder via SSH. Raises warning / critical when oldest/youngest file when that file is older than n days. Also works on BSD.

### SNMP checks

All SNMP checks use SNMP v3

**check_imm2.py*** - Checks IBM IMM2 systems. Can check one of the following things: fan status, temperatures, voltages, sysinfos, disk health, hardware health status. Output is different for all the modules, but usually consists of serial numbers in the output, and performance metrics in the performance data. If WARNING or CRITICAL, the output displays what is broken, so a fan WARNING will have the broken fan in the check output.

**check_synology_snmp.py*** - Only tested on Synology RS815. Can check one of the following things: system status, disk status, raid status, storage utilization, load, memory usage. Output is different for all the modules, but usually consists of serial numbers in the output, and performacne metrics in the performance data. If WARNING or CRITICAL, the output displays what is broken, so a fan WARNING will have the broken fan in the check output.
