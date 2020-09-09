import pytest

import gitlab_trace as gt


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
