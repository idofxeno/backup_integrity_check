__author__ = 'idofxeno'
import sys
import datetime
import subprocess
import argparse
import re

#TO DO: Suppress console output on errors and direct it into logfile

#This utility is designed to be started by cron from an account that will have access
#This utility needs to be run by the root account.  It simply gets a directory listing of the most recent backups
#in a particular directory and lists the contents of each archive to a file.  If reading from the archive throws
#an error, note the error and alter a file in the /tmp directory that is monitored by Zabbix so that an alert can be
#generated


def get_todays_backup_list(today, dir, set):
    command = "find " + dir + " -name '*" + today + "*'"
    dir_list = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    ec = dir_list.wait() #This waits for the process to terminate and returns the exit code
    if ec == 0:
        #TO DO: Refactor logic for simplicity (ec != 0)
        pass
    else:
        #This will edit the backup_integrity file saying the file list could not be parsed
        details_filename = generate_details_filename(set)
        zabbix_filename = generate_zabbix_filename(set)
        with open(details_filename, 'w') as f:
            f.write("Could not parse file list -- exiting")
            f.close()
        with open(zabbix_filename, 'w') as f:
            f.write("1")
            f.close()
        print("Hey, this is broken")
        print(ec)
        sys.exit()

    out, err = dir_list.communicate()
    output = (out.splitlines())


    if set is not None: #set can no longer be 'None', remove this if statement
        if set == 'cfg':
            regex = re.compile(r"env[a-zA-Z]{3}0config\.env\.domain\.com-" + today + "\.tar\.gz")
            filtered = [i for i in output if regex.search(i)]
        else:
            regex = re.compile(r"env[a-zA-Z]{3}\d" + set + "\d\.env\.domain\.com-" + today + "\.tar\.gz")
            filtered = [i for i in output if regex.search(i)]
    return filtered

def generate_zabbix_filename(set):
    filename = '/tmp/backup_integrity_' + set + '.log'
    return filename

def generate_details_filename(set):
    filename = '/tmp/backup_integrity_details_' + set + '.log'
    return filename

def read_archive(archive):
    command = "pigz -d -p 2 < " + archive + " | tar tf -"
    contents = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    ec = contents.wait()
    out, err = contents.communicate()
    #We've read the archive -- append success or failure to success array
    success.append(ec)
    return out

def check_success(success, set):
    #TO DO: Alter the file monitored by Zabbix to fire off an alert if there is a problem
    #TO DO: Alter logfile with message stating that archive was not able to be read
    details_filename = generate_details_filename(set)
    zabbix_filename = generate_zabbix_filename(set)
    for code in success:
        if code == 0:
            #Hey we're all good
            with open(zabbix_filename, 'w') as f:
                f.write("0")
                f.close()
        else:
            with open(details_filename, 'a') as f:
                f.write("\nError:  One or more archives were unable to be read\n")
                f.close()
            with open(zabbix_filename, 'w') as f:
                f.write("1")
                f.close()
                sys.exit() # Exit here so we don't overwrite the monitored file with a success value

#Program starts here
#Parse command line arguments
parser = argparse.ArgumentParser(description='Checks integrity of backup files.')
parser.add_argument('--dir',
                    '-d',
                    required=True,
                    type=str,
                    help='Directory in which to search for backup files.')
parser.add_argument('--set',
                    '-s',
                    required=True,
                    type=str,
                    help='which set to check backups for.  If omitted, will select all backups based on date.')
args = parser.parse_args()

#Make this if not in list, quit.
if args.set == 'a':
    pass
elif args.set == 'b':
    pass
elif args.set == 'cfg':
    pass
else:
    print("Invalid set selection -- Quitting.\n")
    sys.exit()

dir = args.dir
set = args.set

#Get today's date so we get the correct backups
date = datetime.datetime.today()

today = (str(date.strftime('%Y')) +
         str(date.strftime('%m')) +
         str(date.strftime('%d')))

#"Success" array.  This array is checked at the end of the program.  If there are any values other than 0 in the
#array, there was a problem reading one of the archives and we will need to generate an alert
success = []

#get list of all the current day's backups.  Split the output on newlines so we can iterate through the list
backup_list = get_todays_backup_list(today, dir, set)

#set details filename
details_filename = generate_details_filename(set)

#Open a file in append mode and put the result of the tar -tf against the archives into the file
with open(details_filename, 'w') as f:
    f.write("\nDate: " + str(date))
    for backup in backup_list:
        #read archive
        contents = read_archive(backup)
        #output the archive contents into details log file
        #check the return code -- if it's good, do nothing
            #if out return code is bad, edit both logfiles but don't exit (check all files)
            #ALSO, change the file that is monitored by Zabbix so that an alert is fired
        f.write("\nArchive: " + backup + "\n")
        for line in contents:
            f.write(str(line))

#We've written the output from reading the tar archives to a file and added the success value to the array
#Let us now check the success array and see if we need to fire an alert for Zabbix

check_success(success, set)
