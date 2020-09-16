Look at GitLab CI job status from the command line
==================================================

.. image:: https://travis-ci.org/mgedmin/gitlab-trace.svg?branch=master
    :target: https://travis-ci.org/mgedmin/gitlab-trace

.. image:: https://coveralls.io/repos/mgedmin/gitlab-trace/badge.svg?branch=master
    :target: https://coveralls.io/r/mgedmin/gitlab-trace

Sometimes I want to look at the GitLab CI build status from my terminal ::

    $ gitlab-trace
    GitLab project: Foretagsdeklaration/foretagsdeklaration
    Available jobs for pipeline #84214:
       --job=500786 - success - build_server
       --job=500787 - success - build_client
       --job=500788 - success - test_safety
       --job=500789 - success - test_dev_safety
       --job=500790 - success - test_bandit
       --job=500791 - success - test_crontabs
       --job=500792 - success - test_newrelic
       --job=500793 - success - unittests_server
       --job=500794 - success - unittests_client
       --job=500795 - success - build_docker_image
       --job=500796 - failed - test_robot
       --job=500797 - success - test_robot_bolfin

You can take a closer look at a failed job by passing the job ID ::

    $ gitlab-trace --job=500796
    ...
    Uploading artifacts...
    robottests/output: found 540 matching files
    Uploading artifacts to coordinator... ok            id=500796 responseStatus=201 Created token=6yaRqQPr
    ERROR: Job failed: exit code 1

You can look at a different branch ::

    $ gitlab-trace --branch=master
    GitLab project: Foretagsdeklaration/foretagsdeklaration
    https://git.vaultit.org/Foretagsdeklaration/foretagsdeklaration/pipelines/84185
    Available jobs for pipeline #84185:
       --job=500692 - success - build_server
       --job=500693 - success - build_client
       --job=500694 - success - test_safety
       --job=500695 - success - test_dev_safety
       --job=500696 - success - test_bandit
       --job=500697 - success - test_crontabs
       --job=500698 - success - test_newrelic
       --job=500699 - success - unittests_server
       --job=500700 - success - unittests_client
       --job=500701 - success - build_docker_image
       --job=500702 - failed - test_robot
       --job=500703 - success - test_robot_bolfin
       --job=500704 - success - tag_docker_image
       --job=500705 - manual - deploy_stv_managedkube_alpha
       --job=500706 - manual - deploy_id06_alpha
       --job=500707 - manual - deploy_id06_alpha_fs31
       --job=500708 - manual - deploy_id06_beta
       --job=500709 - manual - deploy_id06_beta_fs31
       --job=500710 - manual - deploy_stv_alpha
       --job=500747 - success - test_robot

You can look at a specific pipeline by ID ::

    $ gitlab-trace 84185

You can look at a specific job in that pipeline ::

    $ gitlab-trace 84185 test_robot

If a job has been retried several times you can look at a specific run ::

    $ gitlab-trace 84185 test_robot 1


Installation
------------

``pip3 install --user gitlab-trace`` should take care of everything, just make
sure ~/.local/bin is on your $PATH.

Or you may want to use a script installer like pipx_ (my favourite).


Configuration
-------------

Create a ``~/.python-gitlab.cfg`` like this::

   [global]
   default = mygitlab

   [mygitlab]
   url = https://gitlab.example.com/
   private_token = ...

You can create a private access token in your GitLab profile settings.  It'll
need the "read_api" access scope.


Usage
-----

Help is available via ::

    $ gitlab-trace --help
    usage: gitlab-trace [-h] [--version] [-v] [--debug] [-g NAME] [-p ID]
                        [--job ID] [-b NAME] [PIPELINE-ID] [JOB-NAME] [NTH-JOB-OF-THAT-NAME]

    gitlab-trace: show the status/trace of a GitLab CI pipeline/job.

    positional arguments:
      PIPELINE-ID           select a GitLab CI pipeline by ID (default: the
                            last pipeline of a git branch)
      JOB-NAME              select a GitLab CI pipeline job by name
      NTH-JOB-OF-THAT-NAME  select n-th GitLab CI pipeline job by this name
                            (default: the last one)

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -v, --verbose         print more information
      --debug               print even more information, for debugging
      -g NAME, --gitlab NAME
                            select configuration section in ~/.python-gitlab.cfg
      -p ID, --project ID   select GitLab project ('group/project' or the numeric ID)
      --job ID              show the trace of GitLab CI job with this ID
      -b NAME, --branch NAME, --ref NAME
                            show the last pipeline of this git branch (default:
                            the currently checked out branch)


.. _python-gitlab: https://pypi.org/p/python-gitlab
.. _pipx: https://pipxproject.github.io/pipx/
