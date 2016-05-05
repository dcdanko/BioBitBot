import yaml
from sys import argv
from subprocess import call
from os.path import abspath
import pexpect
import time

def main(args):
    if len(args) == 0 or '-h' in args or '--help' in args:
        print('Usage: report_listing destination_dir')
        return(-1)
    reportListingF = args[0]
    destDir = abspath(args[1])
    with open(reportListingF) as rlf:
        reportListings = yaml.load(rlf)
        for name, rl in reportListings.items():
            kind = rl['kind']
            loc = rl['location']
            reportName = "{}/{}.{}.ibot.html".format(destDir,name,kind)
            cmd = 'cd {}; multiqc --no-data-dir -f -m {} -n {} .'.format(loc, kind,reportName)  
            print(cmd)
            call(cmd,shell=True)
    cmd = 'scp {}/* powrieqc@kviz.kennedy.ox.ac.uk:/home/powrieqc/PowrieQC/powrieqc/ibot_reports'.format(destDir)
    print(cmd)
    child = pexpect.spawn(cmd)
    child.expect("password:")
    time.sleep(0.1)
    child.sendline('zsQS8433Wz2B')
    child.wait()
    


if __name__ == '__main__':
    main(argv[1:])
