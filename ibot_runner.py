import yaml
from sys import argv, stderr
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
        for loc in rlf:
            try:
                loc = loc.strip()
                name = None
                rtype = None
                desc = '_'
                subtype = '_'
                with open("{}/metadata.yml".format(loc)) as mD:
                    mdata = yaml.load(mD)
                    name = mdata['name']
                    rtype = mdata['report_type']
                    if 'description' in mdata:
                        desc = '_'.join(mdata['description'].split())
                    if 'subtype' in mdata:
                        subtype = mdata['subtype']
                reportName = "{}/{}.{}.{}.{}.ibot.html".format(destDir,name,rtype,subtype,desc)
                cmd = 'cd {}; multiqc --no-data-dir -f -m {} -n {} .'.format(loc, rtype,reportName)  
                print("Running: {}".format(cmd))
                out = open('{}/{}.out.log'.format(logDir,name),'w')
                err = open('{}/{}.err.log'.format(logDir,name),'w')
                logfs.append(out)
                logfs.append(err)
                p = Popen(cmd,shell=True,stderr=err,stdout=out)
                ps.append((p,name))
            except Exception as e:
                stderr.write("\033[31mCould not build {}\033[0m\n".format(name))
                e = str(e)
                e = e.split('\n')
                e = ['\t'+el for el in e]
                e = '\n'.join(e)
                stderr.write('\033[33m\tiBot runner encountered an exception:\n{}\n\033[0m'.format(e))


    for p,name in ps:
        p.wait()
        if p.returncode == 0:
            print("\033[94mBuilt {}\033[0m".format(name))
        else:
            stderr.write("\033[31mCould not build {}\033[0m\n".format(name))
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
