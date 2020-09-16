import subprocess
import sys
import textwrap

import pytest

import gitlab_trace as gt


@pytest.fixture(autouse=True)
def mock_gitlab(monkeypatch):
    monkeypatch.setattr(gt, 'gitlab', FakeGitlabModule())


class FakeGitlabModule:
    __version__ = '0.42.frog-knows'

    class Gitlab:
        def __init__(self):
            self.projects = FakeGitlabModule.Projects()

        @classmethod
        def from_config(cls, name=None):
            return cls()

    class Projects:
        def get(self, project_id):
            return FakeGitlabModule.Project(project_id)

    class Project:
        def __init__(self, project_id):
            self.pipelines = FakeGitlabModule.ProjectPipelines()
            self.jobs = FakeGitlabModule.ProjectJobs()
            self.web_url = f'https://git.example.com/{project_id}'

    class ProjectPipelines:
        def list(self, ref=None):
            if ref == 'empty':
                return []
            else:
                return [
                    FakeGitlabModule.ProjectPipeline(1005),
                    FakeGitlabModule.ProjectPipeline(997),
                ]

        def get(self, pipeline_id):
            return FakeGitlabModule.ProjectPipeline(pipeline_id)

    class ProjectPipeline:
        def __init__(self, id):
            self.id = str(id)
            self.jobs = FakeGitlabModule.PipelineJobs(self)

    class PipelineJobs:
        def __init__(self, project_pipeline):
            self._project_pipeline = project_pipeline

        def list(self, all=False):
            if self._project_pipeline.id == '1009':
                return [
                    FakeGitlabModule.ProjectJob(3301, 'build', 'success'),
                    FakeGitlabModule.ProjectJob(3302, 'test', 'failed'),
                    FakeGitlabModule.ProjectJob(3303, 'test', 'failed'),
                    FakeGitlabModule.ProjectJob(3304, 'test', 'running'),
                ]
            else:
                return [
                    FakeGitlabModule.ProjectJob(3201, 'build', 'success'),
                    FakeGitlabModule.ProjectJob(3202, 'test', 'failed'),
                ]

    class ProjectJobs:
        def get(self, job_id):
            return FakeGitlabModule.ProjectJob(job_id, 'build', 'success')

    class ProjectJob:
        def __init__(self, id, name, status):
            self.id = str(id)
            self.name = name
            self.status = status
            self.created_at = '2020-09-16T06:16:49.180Z'
            self.started_at = '2020-09-16T06:16:51.066Z'
            self.finished_at = None
            self.duration = 42
            self.attributes = {"json_attributes": "here"}

        def trace(self):
            return b'Hello, world!\n'


def test_fatal():
    with pytest.raises(SystemExit):
        gt.fatal("oh woe is me")


def test_warn():
    gt.warn("beware hungry bears")


def test_info():
    gt.info("ice cream is yummy")


def test_first():
    assert gt.first([]) is None
    assert gt.first([1]) == 1
    assert gt.first([1, 2, 3]) == 1


def test_pipe():
    assert gt.pipe('echo hello'.split()) == 'hello'


@pytest.mark.parametrize('url, expected', [
    ('https://gitlab.com/owner/project', 'owner/project'),
    ('https://gitlab.com/owner/project.git', 'owner/project'),
    ('https://gitlab.com:443/owner/project.git', 'owner/project'),
    ('ssh://git@gitlab.example.com:23/owner/project.git', 'owner/project'),
    ('https://github.com/owner/project', None),
    ('fridge:git/random.git', None),
])
def test_determine_project(url, expected):
    assert gt.determine_project(url) == expected


def test_determine_project_from_git(monkeypatch):
    monkeypatch.setattr(
        subprocess, 'run',
        lambda *a, **kw: subprocess.CompletedProcess(
            a, 0, stdout='https://gitlab.com/o/p\n')
    )
    assert gt.determine_project() == 'o/p'


def test_determine_branch(monkeypatch):
    monkeypatch.setattr(
        subprocess, 'run',
        lambda *a, **kw: subprocess.CompletedProcess(
            a, 0, stdout='fix-bugs\n')
    )
    assert gt.determine_branch() == 'fix-bugs'


@pytest.mark.parametrize('status, expected', [
    ('success', '\033[32msuccess\033[0m'),
    ('skipped', 'skipped'),
])
def test_fmt_status(status, expected):
    assert gt.fmt_status(status) == expected


@pytest.mark.parametrize('duration, expected', [
    (0, '0s'),
    (1, '1s'),
    (60, '1m'),
    (61, '1m 1s'),
    (3600, '1h'),
    (3601, '1h 1s'),
    (3660, '1h 1m'),
    (3661, '1h 1m 1s'),
    (958.767528, "15m 59s"),
    (None, 'n/a'),
])
def test_fmt_duration(duration, expected):
    assert gt.fmt_duration(duration) == expected


def test_main_help(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '--help'])
    with pytest.raises(SystemExit):
        gt.main()


def test_main_warn_extra_args(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '--job=123', '456'])
    monkeypatch.setattr(gt, 'determine_project', lambda: None)
    with pytest.raises(SystemExit):
        gt.main()
    assert (
        'Ignoring pipeline (456) because --job=123 is specified'
        in capsys.readouterr().err
    )


def test_main_no_project(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace'])
    monkeypatch.setattr(gt, 'determine_project', lambda: None)
    with pytest.raises(SystemExit,
                       match='Could not determine GitLab project ID'):
        gt.main()


def test_main_auto_project(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    with pytest.raises(SystemExit):
        gt.main()
    assert (
        'GitLab project: owner/project'
        in capsys.readouterr().err
    )


def test_main_auto_branch(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    assert (
        'Current branch: main'
        in capsys.readouterr().err
    )


def test_main_no_pipelines(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'empty')
    with pytest.raises(SystemExit,
                       match="Project owner/project doesn't have any pipelines"
                             " for branch empty"):
        gt.main()


def test_main_auto_pipeline(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    assert (
        'https://git.example.com/owner/project/pipelines/1005'
        in capsys.readouterr().err
    )


def test_main_list_jobs(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        Current branch: main
        https://git.example.com/owner/project/pipelines/1005
    """)
    assert stdout == textwrap.dedent("""\
        Available jobs for pipeline #1005:
           --job=3201 - success - build
           --job=3202 - failed - test
    """)


def test_main_job_by_id(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '--job=3202'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
    """)
    assert stdout == textwrap.dedent("""\
        Hello, world!
    """)


def test_main_job_by_name(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '1005', 'test'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        Job ID: 3202
    """)
    assert stdout == textwrap.dedent("""\
        Hello, world!
    """)


def test_main_job_by_name_not_found(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '1005', 'tset'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        Job tset not found
    """)
    assert stdout == textwrap.dedent("""\
        Available jobs for pipeline #1005:
           --job=3201 - success - build
           --job=3202 - failed - test
    """)


def test_main_job_by_name_multiple_last(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '1009', 'test'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'refactoring')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        Found multiple jobs: 3302 3303 3304
        Selecting the last one: 3304
    """)
    assert stdout == textwrap.dedent("""\
        Hello, world!
    """)


def test_main_job_by_name_multiple_nth(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '1009', 'test', '2'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'refactoring')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        Found multiple jobs: 3302 3303 3304
        Selecting #2: 3303
    """)
    assert stdout == textwrap.dedent("""\
        Hello, world!
    """)


def test_main_job_verbose(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '--job=3202', '-v'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        Job created:    2020-09-16T06:16:49.180Z
        Job started:    2020-09-16T06:16:51.066Z
        Job finished:   not yet
        Job duration:   42s
    """)
    assert stdout == textwrap.dedent("""\
        Hello, world!
    """)


def test_main_job_debug(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gitlab-trace', '--job=3202', '--debug'])
    monkeypatch.setattr(gt, 'determine_project', lambda: 'owner/project')
    monkeypatch.setattr(gt, 'determine_branch', lambda: 'main')
    with pytest.raises(SystemExit):
        gt.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == textwrap.dedent("""\
        GitLab project: owner/project
        {
          "json_attributes": "here"
        }
    """)
    assert stdout == textwrap.dedent("""\
        Hello, world!
    """)
