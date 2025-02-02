#!/usr/bin/python3
"""
gitlab-trace: show the status/trace of a GitLab CI pipeline/job.
"""

import argparse
import itertools
import json
import subprocess
import sys
import time
import urllib.parse
from functools import partial
from typing import BinaryIO, Callable, List, Optional, TypeVar

import colorama
import gitlab
import requests.exceptions
from gitlab.v4.objects import ProjectJob


__version__ = '0.8.0.dev0'
__author__ = "Marius Gedminas <marius@gedmin.as>"


T = TypeVar('T')


def fatal(msg: str) -> None:
    sys.exit(msg)


def warn(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def info(msg: str) -> None:
    print(msg, file=sys.stderr)


def pipe(command: List[str]) -> str:
    return subprocess.run(command, stdout=subprocess.PIPE,
                          universal_newlines=True).stdout.rstrip('\n')


def determine_project(url: Optional[str] = None) -> Optional[str]:
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


def fmt_size(size: Optional[float]) -> str:
    if size is None:
        return 'n/a'
    for unit in 'B', 'KiB', 'MiB':
        if size < 1024:
            break
        size /= 1024
    return f'{size:.1f}'.rstrip('0').rstrip('.') + f' {unit}'


def tail(s: bytes, n: Optional[int] = None) -> bytes:
    if not n:
        return s
    return b''.join(s.splitlines(True)[-n:])


def follow(
    job: ProjectJob, buffer: Optional[BinaryIO] = None, interval: float = 1.0,
    tail: Optional[Callable[[bytes], bytes]] = None
) -> None:
    if buffer is None:
        buffer = sys.stdout.buffer
    if tail is None:
        tail = lambda s: s  # noqa: E731
    trace = job.trace()
    buffer.write(tail(trace))
    buffer.flush()
    while not job.finished_at:
        time.sleep(interval)
        job.refresh()
        new_trace = job.trace()
        if not new_trace.startswith(trace):
            # maybe the beginning got truncated?
            warn("\n----- trace was truncated -----")
            trace = ""
        new_data = new_trace[len(trace):]
        if new_data:
            buffer.write(new_data)
            buffer.flush()
        trace = new_trace


def _main() -> None:
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
        "--running", action="store_true",
        help=(
            "show the trace of the currently running GitLab CI job,"
            " if there is one (if there's more than one, picks the first one)"
        ),
    )
    parser.add_argument(
        "-b", "--branch", "--ref", metavar="NAME",
        help=(
            "show the last pipeline of this git branch"
            " (default: the currently checked out branch)"
        ),
    )
    parser.add_argument(
        "-t", "--tail", metavar='N', nargs='?', type=int, const=10,
        help="show the last N lines of the trace log",
    )
    parser.add_argument(
        "-f", "--follow", action="store_true",
        help="periodically poll and output additional logs as the job runs",
    )
    parser.add_argument(
        "--print-url", "--print-uri", action="store_true",
        help="print URL to job page on GitLab instead of printing job's log",
    )
    parser.add_argument(
        "-a", "--artifacts", action="store_true",
        help="download build artifacts",
    )
    parser.add_argument(
        "pipeline", nargs="?", type=int, metavar="PIPELINE-ID",
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

    if args.job and args.running:
        warn(f"Ignoring --running because --job={args.job} was specified")

    if args.job and args.pipeline:
        warn(f"Ignoring pipeline ({args.pipeline})"
             f" because --job={args.job} was specified")

    if not args.project:
        args.project = determine_project()
        if args.project:
            info(f"GitLab project: {args.project}")
        else:
            fatal("Could not determine GitLab project ID")

    gl = gitlab.Gitlab.from_config(args.gitlab)
    project = gl.projects.get(args.project)

    if not args.job and (not args.pipeline or args.pipeline < 0):
        if not args.branch:
            args.branch = determine_branch()
            info(f"Current branch: {args.branch}")

        which = -args.pipeline - 1 if args.pipeline else 0
        pipelines = project.pipelines.list(ref=args.branch, iterator=True)
        skipped = sum(1 for p in itertools.islice(pipelines, which))
        pipeline = next(pipelines, None)
        if pipeline is not None:
            args.pipeline = pipeline.id
            if not args.print_url or args.job_name:
                info(f"{project.web_url}/pipelines/{pipeline.id}")
        else:
            if which == 0:
                fatal(f"Project {args.project} doesn't have any pipelines"
                      f" for branch {args.branch}")
            else:
                fatal(f"Project {args.project} has only {skipped} pipelines"
                      f" for branch {args.branch}")
    elif args.branch:
        if args.job:
            warn(f"Ignoring --branch={args.branch}"
                 f" because --job={args.job} was specified")
        else:
            assert args.pipeline
            warn(f"Ignoring --branch={args.branch}"
                 f" because pipeline ({args.pipeline}) was specified")

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
                info(f"Found multiple jobs: {' '.join(map(str, found))}")
                if args.idx is not None:
                    args.job = found[args.idx - 1]
                    info(f"Selecting #{args.idx}: {args.job}")
                else:
                    args.job = found[-1]
                    info(f"Selecting the last one: {args.job}")
        else:
            if args.debug:
                info(json.dumps(pipeline.attributes, indent=2))
            if args.print_url:
                print(f"{project.web_url}/pipelines/{pipeline.id}")
                sys.exit(0)
        if not args.job:
            print(f"Available jobs for pipeline #{pipeline.id}:")
            for job in jobs:
                status = fmt_status(job.status)
                print(f"   --job={job.id} - {status} - {job.name}")
                if args.running and job.status == 'running' and not args.job:
                    args.job = job.id
                    job_name = job.name
            if args.job:
                info(f"Automatically selected --job={args.job} ({job_name})")
            else:
                if args.running:
                    warn("Ignoring --running because no job was running.")
                if args.artifacts:
                    warn("Ignoring --artifacts because no job was selected.")
                if args.print_url:
                    warn("Ignoring --print-url because no job was selected.")
                sys.exit(0)

    job = project.jobs.get(args.job)
    if args.verbose:
        info(f"Job created:    {job.created_at}")
        info(f"Job started:    {job.started_at or 'not yet'}")
        info(f"Job finished:   {job.finished_at or 'not yet'}")
        info(f"Job duration:   {fmt_duration(job.duration)}")
    if args.debug:
        info(json.dumps(job.attributes, indent=2))
    if args.print_url:
        print(f"{project.web_url}/-/jobs/{job.id}")
    elif args.follow:
        follow(job, tail=partial(tail, n=args.tail))
    else:
        sys.stdout.buffer.write(tail(job.trace(), args.tail))
    if args.artifacts:
        if not hasattr(job, 'artifacts_file'):
            warn("Job has no artifacts.")
            sys.exit(1)
        filename = job.artifacts_file['filename']
        info(f"Artifacts: {filename} ({fmt_size(job.artifacts_file['size'])})")
        with open(filename, "xb") as f:
            job.artifacts(streamed=True, action=f.write)
    sys.exit(0)


def main() -> None:
    try:
        _main()
    except requests.exceptions.RequestException as e:
        sys.exit(str(e))
    except (KeyboardInterrupt, BrokenPipeError):
        # suppress tracebacks from these
        sys.exit(0)


if __name__ == "__main__":
    main()
