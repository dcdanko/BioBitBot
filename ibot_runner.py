import yaml
from sys import argv
from subprocess import Popen
from os.path import abspath
import pexpect
import time

def main(args):
    if len(args) == 0 or '-h' in args or '--help' in args:
        print('Usage: report_listing destination_dir [log_dir]')
        return(-1)
    reportListingF = args[0]
    destDir = abspath(args[1])
    if len(args) > 2:
        logDir = args[2]
    else:
        logDir = '.'
    logfs = []
    ps = []
    with open(reportListingF) as rlf:
        reportListings = yaml.load(rlf)
        for name, rl in reportListings.items():
            kind = rl['kind']
            loc = rl['location']
            reportName = "{}/{}.{}.ibot.html".format(destDir,name,kind)
            cmd = 'cd {}; multiqc --no-data-dir -f -m {} -n {} .'.format(loc, kind,reportName)  
            print("Running: {}".format(name))
            out = open('{}/{}.out.log'.format(logDir,name),'w')
            err = open('{}/{}.err.log'.format(logDir,name),'w')
            logfs.append(out)
            logfs.append(err)
            p = Popen(cmd,shell=True,stderr=err,stdout=out)
            ps.append((p,name))
    for p,name in ps:
        p.wait()
        if p.returncode == 0:
            print("\033[94mBuilt {}\033[0m".format(name))
        else:
            print("\033[93mCould not build {}\033[0m".format(name))
    for lf in logfs:
        lf.close()
    cmd = 'scp {}/* powrieqc@kviz.kennedy.ox.ac.uk:/home/powrieqc/PowrieQC/powrieqc/ibot_reports'.format(destDir)
    print(cmd)
    child = pexpect.spawn(cmd)
    child.expect('(?i)password')
    passcode = 'zsQS8433Wz2B'
    child.sendline(passcode)
    print(passcode)
    child.wait()
    


if __name__ == '__main__':
    main(argv[1:])
