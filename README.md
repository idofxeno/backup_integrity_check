# backup_integrity_check
Reads the contents of compressed tar archives and outputs results to files

Requirements: Python 2.6.6+, pigz
Usage: python backup_integrity_check.py [-h] --dir DIR --set SET

This utility is designed to be started by cron from an account that will have access to the files in the directory that is
passed in on the command line.  A list of files in the directory is generated, and then filtered with a list comprehension based
on the set that is passed in on the command line.  Based on that list, each tar archive is decompressed and the files within
each are read and the output is stored into a log file appended with the name of the set.  After all files have been processed, 
another log file is created (also appended with the name of the set) that holds a 0 if all archives were successfully able to be read, and a 1 if there were any issues.  This file would be monitored by Zabbix or some other monitoring agent, firing off an alert if the value held in the file was not 0, letting you know one of your backups may have an issue.  You can modify the list of sets as well as the regex and list comprehensions to suit the particular naming conventions of your environment.

*TO DO: Make set parameter optional, just grabbing files based off of date within specified dir
