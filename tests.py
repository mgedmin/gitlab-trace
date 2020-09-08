import pytest

from gitlab_trace import determine_project, first


def test_first():
    assert first([]) is None
    assert first([1]) == 1
    assert first([1, 2, 3]) == 1


@pytest.mark.parametrize('url, expected', [
    ('https://gitlab.com/owner/project', 'owner/project'),
    ('https://gitlab.com/owner/project.git', 'owner/project'),
    ('https://gitlab.com:443/owner/project.git', 'owner/project'),
    ('ssh://git@gitlab.example.com:23/owner/project.git', 'owner/project'),
])
def test_determine_project(url, expected):
    assert determine_project(url) == expected
