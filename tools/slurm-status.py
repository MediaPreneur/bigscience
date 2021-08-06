#!/usr/bin/env python

#
# This tool reports on the status of the job - whether it's running or scheduled and various other useful data
#
# Example:
#
# slurm-status.py --job-name tr1-13B-round3.slurm
#

import argparse
import io
import json
import os
import re
import subprocess
import sys
import shlex
from datetime import datetime, timedelta

def run_cmd(cmd):
    try:
        git_status = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True,
            encoding="utf-8",
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise EnvironmentError(exc.stderr)

    return git_status


def get_slurm_group_status():
    # we need to monitor slurm jobs of the whole group six, since the slurm job could be owned by
    # any user in that group
    group = "six"
    cmd = f"getent group {group}"
    getent = run_cmd(cmd.split())
    # six:*:3015222:foo,bar,tar
    usernames = getent.split(':')[-1]

    # get all the scheduled and running jobs
    # use shlex to split correctly and not on whitespace
    cmd = f'squeue --user={usernames} -o "%.16i %.9P %.40j %.8T %.10M %.6D %.20S %R"'
    data = run_cmd(shlex.split(cmd))
    lines = [line.strip() for line in data.split("\n")]
    return lines

def get_remaining_time(time_str):
    """
    slurm style time_str = "2021-08-06T15:23:46"
    """

    delta = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S") - datetime.now()
    # round micsecs
    delta -= timedelta(microseconds=delta.microseconds)
    return delta

def process_job(jobid, partition, name, state, time, nodes, start_time, notes):
    if state == "RUNNING":
        print(f"{name} is running for {time} since {start_time} ({jobid} on '{partition}' partition ({notes})")
    elif state == "PENDING":
        remaining_wait_time = get_remaining_time(start_time)
        print(f"{name} is scheduled to start in {remaining_wait_time} (at {start_time}) ({jobid} on '{partition}' partition)")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-name", type=str, required=True, help="slurm job name")
    parser.add_argument("-d", "--debug", action='store_true', help="enable debug")
    return parser.parse_args()

def main():

    args = get_args()
    status_lines = get_slurm_group_status()

    for l in status_lines:
        #print(f"l=[{l}]")
        jobid, partition, name, state, time, nodes, start_time, notes = l.split()
        if name == args.job_name:
            process_job(jobid, partition, name, state, time, nodes, start_time, notes)


if __name__ == "__main__":

    main()
