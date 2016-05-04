import yaml
from sys import argv
from subprocess import call
from os.path import abspath


def main(args):
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
            


if __name__ == '__main__':
    main(argv[1:])
