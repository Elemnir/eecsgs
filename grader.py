#!/usr/bin/env python

"""grader.py: A tool for automating grading of gradescript labs"""

#from __future__ import print_function

import argparse
import datetime
import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time

__author__      = "Adam Howard"
__copyright__   = "Copyright 2016, University of Tennessee"
__credits__     = ["Adam Howard", "Ben Olson"]
__license__     = "BSD 3-Clause"
__version__     = "0.1.0"
__email__       = "ahowar31@vols.utk.edu"

# Python 2/3 Support
if sys.version_info[0] == 2:
    input = raw_input
    range = xrange
    str   = unicode

class SubInfo(object):
    def __init__(self, stu, sdir, stime):
        self.name  = stu
        self.path  = sdir
        self.stime = stime
        self.gspts = 0
        self.stpts = 'N/A'
        self.notes = []

    def __repr__(self):
        return "{:<8} {:>5} {:>5} {}\n".format(
            self.name, self.gspts, self.stpts,
            "\n                     ".join(self.notes) if self.notes else ""
        )

    def __lt__(self, other):
        return self.name < other.name


def logmsg(msg):
    """Logs `msg` to a file and stdout"""
    logging.info(msg)
    print(msg)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gradescripted Lab Grading Tool."
    )

    parser.add_argument('--due', metavar='TIME',
        required=True,
        type=lambda s: datetime.datetime.strptime(s, "%m/%d/%Y %H:%M"),
        help='Due date as a string ("01/30/2016 23:30")'
    )
    
    parser.add_argument('--labpath', metavar='PATH',
        required=True,
        help='Path to the provided lab files'
    )
    
    parser.add_argument('--sourcefiles', metavar='FILES',
        required=True,
        type=lambda s: s.split(','),
        help='Comma Separated list of files to be extracted from submission'
    )
    
    parser.add_argument('--compcmds', metavar='CMDS',
        default='make',
        type=lambda s: s.split(','),
        help='Comma separated list of compilation commands to be executed'
    )

    parser.add_argument('--commonfiles', metavar='FILES',
        default=[],
        type=lambda s: s.split(','),
        help='Comma Separated list of files provided by the lab'
    )

    def rangesplit(s):
        l = map(int, s.split('-'))
        return l if len(l) <= 1 else range(l[0], l[1]+1)
    parser.add_argument('--probset', metavar='PROBS',
        default=None,
        type=lambda s: [x for r in s.split(',') for x in rangesplit(r)],
        help='Comma separated list of problems to run, defaults to all (1-5,15,17,20-25)'
    )
    
    parser.add_argument('--reportfile', metavar='FILE',
        default=sys.stdout, 
        type=argparse.FileType('w'),
        help='Write the final report to FILE, defaults to stdout'
    )

    return parser.parse_args()


def extract_sources(tarname, sourcefiles):
    """Extracts given sourcefiles from a tarball named `tarname`
    
    returns a relevant SubInfo instance
    """
    lab, cls, stu, sub, ext = tarname.split('.')
    tar = tarfile.open(tarname)
    sdir = "{}_{}_{}".format(lab,cls,stu)
    for src in sourcefiles:
        name = os.path.join(sdir, src)
        try:
            tar.extract(name)
        except KeyError as ke:
            print(ke)
            tar.list(verbose=False)
            wrongname = input("> ")
            tar.extract(wrongname)
            os.rename(wrongname, name)
    
    return SubInfo(stu, sdir, datetime.datetime.fromtimestamp(int(sub)))


def grade_submission(info, gspath, compcmds, problems=None, gatimeout=600, gstimeout=120):
    """Attempts to compile and then run gradescripts for the given SubInfo.
    
    Records the number correct and also notes compilation failure in `info`.

    If problems is provided that subset of gradescripts will be run, otherwise,
    gradeall will be executed.
    """
   
    # Attempt all compilation commands
    logmsg("Compiling {}'s submission".format(info.name))
    for cmd in compcmds:
        rval = subprocess.call(cmd, shell=True)
        if rval != 0:
            info.notes.append("Compilation Failed: {}".format(cmd))

    def poll_until_timeout(proc, timeout):
        """Waits on `proc` for a max of `timeout` seconds
        Returns True if the timeout was reached.
        """
        for i in range(timeout):
            if proc.poll() != None:
                return False
            time.sleep(1)
        return True

    # Run the Gradescripts
    logmsg("Grading {}'s submission".format(info.name))
    buf = str()
    if not problems:
        gscript = os.path.join(gspath, "gradeall")
        proc = subprocess.Popen(gscript, shell=True, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if poll_until_timeout(proc, gatimeout):
            info.notes.append("Gradeall Timed Out")
            proc.kill()
        buf += proc.communicate()[0]
    else:
        for prob in problems:
            gscript = "{} {}".format(os.path.join(gspath, "gradescript"), prob)
            proc = subprocess.Popen(gscript, shell=True, universal_newlines=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if poll_until_timeout(proc, gstimeout):
                info.notes.append("Gradescript {} Timed Out".format(prob))
                proc.kill()
            buf += proc.communicate()[0]

    # Count up the number of correct gradescripts
    info.gspts = len(re.findall(r'Problem \d+ is correct\.', buf))
    logmsg("Complete. Got {}".format(info.gspts))


def view_submission(info):
    """Opens each of the files in a student's submission so the grader can 
    inspect them. Provides notes and grade information for the student, then
    allows the grader to provide a style point score and notes.
    """
    print(info)
    input("<Press Enter to view files>")
    for fname in glob.glob("{}/*".format(info.path)):
        subprocess.call("less {}".format(fname), shell=True)
    info.stpts = input("Style Points: ")
    notes = input("Notes: ")
    if notes:
        info.notes.append(notes)


def grade_all():
    """Grades all tarballs of the form <lab>.<class>.<netid>.<subtime>.tgz 
    in the current directory.
    """
    logging.basicConfig(filename='grades.log', filemode='w', level=logging.INFO)
    
    # Parse arguments
    args = parse_args()
    
    # Extract all tarballs and collect submission info
    logmsg("Extracting submission files...")
    subs = []
    for tarball in glob.glob("*.tgz"):
        si = extract_sources(tarball, args.sourcefiles)
        subs.append(si)
    logmsg("Found {} submissions.".format(len(subs)))

    # Create the working directory and copy in common files
    if (os.path.exists("tmp")):
        shutil.rmtree("tmp")
    os.mkdir("tmp")
    for fname in args.commonfiles:
        shutil.copy(os.path.join(args.labpath,fname), "tmp")
    os.chdir("tmp")

    # Execute Gradescripts
    logmsg("Grading submissions...")
    for si in subs:
        # Copy in the student's submission
        for src in glob.glob("../{}/*".format(si.path)):
            shutil.copy(src, ".")
 
        # Compile and run the gradescripts
        grade_submission(si, args.labpath, args.compcmds, args.probset)
        
        # Clean out everything but helper files
        for jnk in glob.glob("./*"):
            if jnk not in args.sourcefiles:
                os.remove(jnk)
    
    # Leave the temporary directory
    os.chdir("..")

    # Mark Late Labs
    for si in subs:
        if si.stime > args.due:
            td = si.stime - args.due
            si.notes.append("Late Submission: {} days, {:.2f} hours".format(td.days, td.seconds/3600.0))

    # Open code files for grader inspection
    logmsg("Beginning code review...")
    for si in subs:
        view_submission(si)

    # Create Report
    logmsg("Writing Report...")
    args.reportfile.write("\n{:8} {:>5} {:>5} {}\n".format(
        "Netid", "#GSs", "Style", "Notes"))
    for si in sorted(subs):
        args.reportfile.write(repr(si))


if __name__ == "__main__":
    grade_all()
