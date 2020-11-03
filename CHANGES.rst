Changelog
==========

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
