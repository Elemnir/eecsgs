#!/usr/bin/env python

"""submit.py: A tool for packaging and submitting labs"""

__author__      = "Adam Howard"
__copyright__   = "Copyright 2016, University of Tennessee"
__credits__     = ["Adam Howard"]
__license__     = "BSD 3-Clause"
__version__     = "0.1.0"
__email__       = "ahowar31@vols.utk.edu"

import argparse
import glob
import json
import os
import shutil
import sys
import tarfile
import textwrap
import time

# Python 2/3 Support
if sys.version_info[0] == 2:
    input = raw_input
    range = xrange
    str   = unicode


def parse_args():
    parser = argparse.ArgumentParser(
        description="Lab assignment submission tool."
    )
    parser.add_argument("config", help="Path to a course config JSON file")
    return parser.parse_args()


def submit():
    """Tar and email the current directory to the course TA."""
    args = parse_args()
    
    # get the course's configuration
    with open(args.config) as cfgfile:
        cfg = json.load(cfgfile)
    
    # Confirm the correct directory
    wdir = os.getcwd()
    resp = input("The current directory is:\n\n\t" + wdir 
                + "\n\nIs this the directory you want to submit? (y/n): ")
    if resp not in ["y", "Y", "yes", "Yes", "YES"]:
        return
    
    # Get the assignment the student is submitting
    resp = ""
    while resp not in cfg["assignments"]:
        resp = input("Select an assignment from the list:\n\n\t" 
                    + "\n\t".join(textwrap.wrap(", ".join(cfg["assignments"])))
                    + "\n\nAssignment: ")
    assignment = resp

    # Get the section to which the user wants to submit
    resp = ""
    desc = "\n\t".join(["{:3}: {}".format(key, cfg["sections"][key]["desc"]) 
                        for key in cfg["sections"].keys()])
    while resp not in cfg["sections"].keys():
        resp = input("Select a section number from the list:\n\n\t" 
                    + desc + "\n\nSection: ")
    section = resp

    # Collect the username and list of files to tar
    username = os.environ.get("USER")
    files = glob.glob("*")

    # Create the submission directory and copy in all the files
    submitdir = "{}_{}_{}".format(assignment, cfg["course"], username)
    os.mkdir(submitdir)
    for f in files:
        shutil.copy(f, os.path.join(submitdir, f))

    # Create the archive, then delete the submission directory
    tarname = "{}.{}.{}.{}.tgz".format(assignment, cfg["course"], 
                                       username, int(time.time()))
    with tarfile.open(tarname, mode="w:gz") as tar:
        tar.add(submitdir)
    shutil.rmtree(submitdir)

    # Perform the submission
    
   

if __name__ == "__main__":
    submit()
