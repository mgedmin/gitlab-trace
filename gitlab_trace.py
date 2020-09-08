#!/usr/bin/python3
"""
gitlab-trace: show the status/trace of a GitLab CI pipeline/job.
"""

import argparse
import sys
import subprocess
import urllib.parse

# pip install python-gitlab
import gitlab


__version__ = "0.2.0"
__author__ = "Marius Gedminas <marius@gedmin.as>"


def fatal(msg):
    sys.exit(msg)


def warn(msg):
    print(msg, file=sys.stderr)


def info(msg):
    print(msg, file=sys.stderr)


def first(seq, default=None):
    return next(iter(seq), default)


def determine_project(url=None):
    if not url:
        url = subprocess.run('git remote get-url origin'.split(),
                             capture_output=True, text=True).stdout.strip()
    if '://' not in url:
        return None
    if urllib.parse.urlparse(url).hostname in ('', 'github.com'):
        return None
    project = urllib.parse.urlparse(url).path.strip('/')
    if project.endswith('.git'):
        project = project[:-len('.git')]
    return project


def determine_branch():
    return subprocess.run('git symbolic-ref HEAD --short'.split(),
                          capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version", action="version",
        version=", ".join([
            f"%(prog)s version {__version__}",
            f"python-gitlab version {gitlab.__version__}"
        ]),
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="print more information",
    )
    parser.add_argument(
        "-g", "--gitlab", metavar="NAME",
        help="select configuration section in ~/.python-gitlab.cfg",
    )
    parser.add_argument(
        "-p", "--project", metavar="ID",
        help="select GitLab project ('group/project' or the numeric ID)",
    )
    parser.add_argument(
        "--job", metavar="ID",
        help="show the trace of GitLab CI job with this ID",
    )
    parser.add_argument(
        "-b", "--branch", "--ref", metavar="NAME",
        help=(
            "show the last pipeline of this git branch"
            " (default: the currently checked out branch)"
        ),
    )
    parser.add_argument(
        "pipeline", nargs="?", metavar="PIPELINE-ID",
        help=(
            "select a GitLab CI pipeline by ID"
            " (default: the last pipeline of a git branch)"
        ),
    )
    parser.add_argument(
        "job_name", nargs="?", metavar="JOB_NAME",
        help="select a GitLab CI pipeline job by name",
    )
    parser.add_argument(
        "idx", nargs='?', metavar="NTH-JOB-OF-THAT-NAME", type=int,
        help=(
            "select n-th GitLab CI pipeline job by this name"
            " (default: the last one)"
        ),
    )
    args = parser.parse_args()

    if args.job and args.pipeline:
        warn(f"Ignoring pipeline ({args.pipeline})"
             f" because --job={args.job} is specified")

    if not args.project:
        args.project = determine_project()
        if args.project:
            info(f"GitLab project: {args.project}")
        else:
            fatal("Could not determine GitLab project ID")

    gl = gitlab.Gitlab.from_config(args.gitlab)
    project = gl.projects.get(args.project)

    if not args.job and not args.pipeline:
        if not args.branch:
            args.branch = determine_branch()
            info(f"Current branch: {args.branch}")

        pipeline = first(project.pipelines.list(ref=args.branch))
        if pipeline:
            args.pipeline = pipeline.id
            info(f"{project.web_url}/pipelines/{pipeline.id}")
        else:
            fatal(f"Project {args.project} doesn't have any pipelines"
                  f" for branch {args.branch}")

    if not args.job:
        pipeline = project.pipelines.get(args.pipeline)
        jobs = list(pipeline.jobs.list())
        if args.job_name:
            found = [job.id for job in jobs if job.name == args.job_name]
            if not found:
                warn(f"Job {args.job_name} not found")
            elif len(found) == 1:
                args.job = found[0]
                info(f"Job ID: {args.job}")
            else:
                info(f"Found multiple jobs: {' '.join(found)}")
                if args.idx is not None:
                    args.job = found[args.idx - 1]
                    info(f"Selecting #{args.idx}: {args.job}")
                else:
                    args.job = found[-1]
                    info(f"Selecting the last one: {args.job}")
        if not args.job:
            info(f"Available jobs for pipeline #{pipeline.id}:")
            for job in jobs:
                print(f"   --job={job.id} - {job.status} - {job.name}")
            sys.exit(0)

    job = project.jobs.get(args.job)
    sys.stdout.buffer.write(job.trace())


if __name__ == "__main__":
    main()
