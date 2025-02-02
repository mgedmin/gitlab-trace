Changelog
==========

0.8.0 (unreleased)
------------------

- Drop Python 3.7 support.


0.7.2 (2024-10-09)
------------------

- Add Python 3.13 support.


0.7.1 (2023-10-09)
------------------

- Add Python 3.12 support.
- Show the name of the automatically selected job when using ``--running`` 
- Shorter output for network errors (suppress tracebacks, print just the error
  itself).
- Fix DeprecationWarning: ``as_list=False`` is deprecated and will be removed in
  a future version. Use ``iterator=True`` instead.


0.7.0 (2023-03-09)
------------------

- ``-t``/``--tail [N]`` for showing the last N lines of the trace log.
- ``-f``/``--follow`` for following a job as it runs.
- ``--running`` for automatically selecting the first running job.


0.6.2 (2022-12-13)
------------------

- Fix UserWarning: Calling a ``list()`` method without specifying ``all=True`` or
  ``as_list=False`` will return a maximum of 20 items from python-gitlab.  Should
  now support choosing 21st or more pipeline from the end when invoked as
  gitlab-trace -21 etc.


0.6.1 (2022-10-27)
------------------

- Gracefully handle a job having no artifacts instead of spewing chained
  tracebacks.
- Add Python 3.10 and 3.11 support.
- Drop Python 3.6 support.


0.6.0 (2020-11-03)
------------------

- Warn about unused command-line arguments (--branch when --job or
  pipeline is specified, --artifacts when no job is specified).
- Allow referring to the Nth latest pipeline with -1, -2, -3 instead
  of the pipeline number.
- Fix TypeError: sequence item 0: expected str instance, int found
  while printing "Found multiple jobs"
- ``--print-url`` for printing the job's or pipeline's URL instead of dumping
  the log/list of jobs.
- ``--debug`` now works for pipelines as well.
- Add Python 3.9 support.


0.5.0 (2020-09-18)
------------------

- Suppress tracebacks for keyboard interrupt or broken pipe errors.
- ``-a``/``--artifacts`` for downloading a job's artifacts.zip to the current
  working directory.


0.4.0 (2020-09-16)
------------------

- 100% test coverage.
- Fixes for Python 3.6 compatibility (subprocess.run() doesn't
  accept 'text' or 'capture_output' keyword arguments).
- ``--verbose`` shows job start/finish times and duration on stderr.
- ``--debug`` for seeing raw JSON data available from GitLab API.


0.3.0 (2020-09-09)
------------------

- Colorized job status output.
- Do not ignore jobs beyond the first batch of 20.


0.2.0 (2020-09-08)
------------------

- Ported to Python, made it 2x faster.
- First PyPI release.


0.1.0 (unreleased)
------------------

- gitlab-trace was a bash script in my scripts repository:
  https://github.com/mgedmin/scripts/blob/1e673264db3678b473f9269b27e5e9994942fc4b/gitlab-trace
