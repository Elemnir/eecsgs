#!/usr/bin/env python

"""submit.py: A tool for packaging and submitting labs"""

__author__      = "Adam Howard"
__copyright__   = "Copyright 2016, University of Tennessee"
__credits__     = ["Adam Howard"]
__license__     = "BSD 3-Clause"
__version__     = "0.1.0"
__email__       = "ahowar31@vols.utk.edu"

import argparse
import datetime
import email.mime.base
import email.mime.multipart
import email.mime.text
import glob
import hashlib
import json
import os
import shutil
import smtplib
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
    subtime = datetime.datetime.now()
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
        resp = input("\nSelect an assignment from the list:\n\n\t" 
                    + "\n\t".join(textwrap.wrap(", ".join(cfg["assignments"])))
                    + "\n\nAssignment: ")
    assignment = resp

    # Get the section to which the user wants to submit
    resp = ""
    desc = "\n\t".join(["{:3}: {}".format(key, cfg["sections"][key]["desc"]) 
                        for key in cfg["sections"].keys()])

    while resp not in cfg["sections"].keys():
        resp = input("\nSelect a section number from the list:\n\n\t" 
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
    tarname = "{}.{}.{}.{}.tgz".format(
        assignment, cfg["course"], username, int(time.time())
    )
    with tarfile.open(tarname, mode="w:gz") as tar:
        tar.add(submitdir)
    shutil.rmtree(submitdir)

    # Build the email headers
    faddr = "{}@eecs.utk.edu".format(username)
    taddr = "{}@eecs.utk.edu".format(cfg["sections"][section]["ta"])
    
    msg = email.mime.multipart.MIMEMultipart()
    msg["From"] = faddr
    msg["To"] = taddr
    msg["Subject"] = "{} submission for student {} in {}".format(
        assignment, username, cfg["course"]
    )

    # Build the attachment and compute a check sum
    attachment = email.mime.base.MIMEBase('application', 'octet-stream')
    with open(tarname, 'rb') as f:
        contents = f.read()
        chksum = hashlib.md5(contents).hexdigest()
        attachment.set_payload(contents)
    
    email.encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", 
        "attachment; filename={}".format(tarname)
    )
    msg.attach(attachment)
    
    # Build and attach the message text
    msg.attach(email.mime.text.MIMEText(
          "Submission from {}\n".format(username)
        + "Course: {}\n".format(cfg["course"])
        + "Assignment: {}\n".format(assignment)
        + "Time: {}\n".format(subtime.strftime("%m/%d/%Y %H:%M:%S"))
        + "MD5Sum: {}\n".format(chksum),
        "plain"))
   
    # Send the email
    server = smtplib.SMTP('localhost')
    server.sendmail(faddr, [taddr], msg.as_string())
    server.quit()

if __name__ == "__main__":
    submit()
