Changelog
==========

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
