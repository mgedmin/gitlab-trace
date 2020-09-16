#!/usr/bin/python3
"""
gitlab-trace: show the status/trace of a GitLab CI pipeline/job.
"""

import argparse
import json
import subprocess
import sys
import urllib.parse
from typing import Iterable, List, Optional, TypeVar

import colorama
import gitlab


__version__ = '0.4.0'
__author__ = "Marius Gedminas <marius@gedmin.as>"


T = TypeVar('T')


def fatal(msg: str) -> None:
    sys.exit(msg)


def warn(msg: str) -> None:
    print(msg, file=sys.stderr)


def info(msg: str) -> None:
    print(msg, file=sys.stderr)


def first(seq: Iterable[T], default: Optional[T] = None) -> Optional[T]:
    return next(iter(seq), default)


def pipe(command: List[str]) -> str:
    return subprocess.run(command, stdout=subprocess.PIPE,
                          universal_newlines=True).stdout.rstrip('\n')


def determine_project(url: str = None) -> Optional[str]:
    if not url:
        url = pipe('git remote get-url origin'.split())
    if '://' not in url:
        return None
    if urllib.parse.urlparse(url).hostname in ('', 'github.com'):
        return None
    project = urllib.parse.urlparse(url).path.strip('/')
    if project.endswith('.git'):
        project = project[:-len('.git')]
    return project


def determine_branch() -> str:
    return pipe('git symbolic-ref HEAD --short'.split())


def fmt_status(status: str) -> str:
    colors = {
        'success': colorama.Fore.GREEN,
        'failed': colorama.Fore.RED,
        'running': colorama.Fore.YELLOW,
        'pending': colorama.Fore.MAGENTA,
        'created': colorama.Fore.CYAN,
        'manual': colorama.Fore.BLUE,
    }
    if status not in colors:
        return status
    return colors[status] + status + colorama.Style.RESET_ALL


def fmt_duration(duration: Optional[float]) -> str:
    if duration is None:
        return 'n/a'
    m, s = divmod(round(duration), 60)
    h, m = divmod(m, 60)
    bits = []
    if h:
        bits.append(f"{h}h")
    if m:
        bits.append(f"{m}m")
    if s or not bits:
        bits.append(f"{s}s")
    return " ".join(bits)


def main() -> None:
    colorama.init()

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
        "--debug", action="store_true",
        help="print even more information, for debugging",
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
        "job_name", nargs="?", metavar="JOB-NAME",
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
        jobs = list(pipeline.jobs.list(all=True))
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
            print(f"Available jobs for pipeline #{pipeline.id}:")
            for job in jobs:
                status = fmt_status(job.status)
                print(f"   --job={job.id} - {status} - {job.name}")
            sys.exit(0)

    job = project.jobs.get(args.job)
    if args.verbose:
        info(f"Job created:    {job.created_at}")
        info(f"Job started:    {job.started_at or 'not yet'}")
        info(f"Job finished:   {job.finished_at or 'not yet'}")
        info(f"Job duration:   {fmt_duration(job.duration)}")
    if args.debug:
        info(json.dumps(job.attributes, indent=2))
    sys.stdout.buffer.write(job.trace())
    sys.exit(0)


if __name__ == "__main__":
    main()
