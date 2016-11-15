#!/usr/bin/env python

"""grader.py: A tool for automating grading of gradescript labs"""

#from __future__ import print_function

__author__      = "Adam Howard"
__copyright__   = "Copyright 2016, University of Tennessee"
__credits__     = ["Adam Howard", "Ben Olson"]
__license__     = "BSD 3-Clause"
__version__     = "0.1.0"
__email__       = "ahowar31@vols.utk.edu"

import argparse
import datetime
import glob
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time

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
    sys.stdout.write(msg+'\n')

logging.basicConfig(filename='grades.log', filemode='w', level=logging.INFO)


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
    
    parser.add_argument('--gatimeout', metavar='SECONDS',
        default=240, type=int,
        help='Number of seconds to allow Gradeall to run, has no effect when using --probset'
    )
    
    parser.add_argument('--gstimeout', metavar='SECONDS',
        default=30, type=int,
        help='Number of seconds to allow each gradescript to run, only works with --probset'
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
            sys.stdout.write(repr(ke)+'\n')
            tar.list(verbose=False)
            wrongname = input("Enter file name or NONE> ")
            if wrongname != "NONE":
                tar.extract(wrongname)
                os.rename(wrongname, name)
    
    return SubInfo(stu, sdir, datetime.datetime.fromtimestamp(int(sub)))


def grade_submission(info, gspath, compcmds, problems=None, gatimeout=240, gstimeout=30):
    """Attempts to compile and then run gradescripts for the given SubInfo.
    
    Records the number correct and also notes compilation failure in `info`.

    If problems is provided that subset of gradescripts will be run, otherwise,
    gradeall will be executed.
    """
    def run_timed_subprocess(cmd, timeout):
        """Run `cmd` as a subprocess for `timeout` seconds
        Returns the subprocess's stdout and stderr as a tuple
        """
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                preexec_fn=os.setsid, close_fds=True)
        for i in range(timeout):
            if proc.poll() != None:
                break
            time.sleep(1)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            logmsg("Gradescript Timeout: {}".format(cmd))
        
        out, err = proc.communicate()
        return out, err

    # Attempt all compilation commands
    logmsg("Compiling {}'s submission".format(info.name))
    for cmd in compcmds:
        out, err = run_timed_subprocess(cmd, 120)
        if (out and "error" in out) or (err and "error" in err):
            info.notes.append("Compilation Failed: {}".format(cmd))
            logmsg("Compilation Failed: {}".format(cmd))

    # Run the Gradescripts
    logmsg("Grading {}'s submission".format(info.name))
    buf = str()
    if not problems:
        gscript = os.path.join(gspath, "gradeall")
        buf += run_timed_subprocess(gscript, gatimeout)[0]
    else:
        for prob in problems:
            gscript = "{} {}".format(os.path.join(gspath, "gradescript"), prob)
            buf += run_timed_subprocess(gscript, gstimeout)[0]

    # Count up the number of correct gradescripts
    info.gspts = len(re.findall(r'Problem \d+ is correct\.', buf))
    logmsg("Complete. Got {}".format(info.gspts))


def view_submission(info):
    """Opens each of the files in a student's submission so the grader can 
    inspect them. Provides notes and grade information for the student, then
    allows the grader to provide a style point score and notes.
    """
    sys.stdout.write(repr(info)+'\n')
    input("<Press Enter to view files>")
    for fname in glob.glob("{}/*".format(info.path)):
        subprocess.call("less {}".format(fname), shell=True)
    info.stpts = input("Style Points: ")
    notes = input("Notes: ")
    while notes != "":
        info.notes.append(notes)
        notes = input("Notes: ")


def grade_all(args):
    """Grades all tarballs of the form <lab>.<class>.<netid>.<subtime>.tgz 
    in the current directory.
    """
    
    # Extract all tarballs and collect submission info
    logmsg("Extracting submission files...")
    subs = []
    for tarball in glob.glob("*.tgz"):
        si = extract_sources(tarball, args.sourcefiles)
        subs.append(si)
    subs.sort()
    logmsg("Found {} submissions.".format(len(subs)))

    # Create the working directory and copy in common files
    if (os.path.exists("tmp")):
        shutil.rmtree("tmp")
    os.mkdir("tmp")
    for fname in args.commonfiles:
        logmsg("Copying common file: {}".format(fname))
        shutil.copy(os.path.join(args.labpath,fname), "tmp")
    os.chdir("tmp")

    # Execute Gradescripts
    logmsg("Grading submissions...")
    for si in subs:
        # Copy in the student's submission
        for src in glob.glob("../{}/*".format(si.path)):
            shutil.copy(src, ".")
 
        # Compile and run the gradescripts
        grade_submission(si, args.labpath, args.compcmds, args.probset,
                         args.gatimeout, args.gstimeout)
        
        # Clean out everything but helper files
        for jnk in glob.glob("*"):
            if jnk not in args.commonfiles:
                if os.path.isdir(jnk):
                    shutil.rmtree(jnk)
                else:
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
    for si in subs:
        args.reportfile.write(repr(si))


if __name__ == "__main__":
    args = parse_args()
    grade_all(args)
