import pytest

from rdopkg.cli import rdopkg
from rdopkg.actions.release.actions import *
from rdopkg.exception import UserAbort

import test_common as common


def test_release_raises_when_release_and_repos_options():
    with pytest.raises(UserAbort):
        release(release_specified='rel-1', repo='repo-1')


def test_release_with_repo_option_1(tmpdir, capsys):
    rdoinfo_path = common.prep_rdoinfo_test(tmpdir, 'sample-1')
    rv = release(local_info=rdoinfo_path, repo='el9s')
    cap = capsys.readouterr()
    output = cap.out
    assert "zed" in output
    assert "yoga" in output
    assert "xena" in output
    assert "wallaby" in output
    assert "victoria" not in output
    assert "ussuri" not in output


def test_release_with_repo_option_2_not_a_known_value(tmpdir, capsys):
    rdoinfo_path = common.prep_rdoinfo_test(tmpdir, 'sample-1')
    rv = release(local_info=rdoinfo_path, repo='not-a-known-value')
    cap = capsys.readouterr()
    output = cap.out
    assert "zed" not in output
    assert "yoga" not in output
    assert "xena" not in output
    assert "wallaby" not in output
    assert "victoria" not in output
    assert "ussuri" not in output


def test_release_with_repo_option_3_empty_value(tmpdir, capsys):
    rdoinfo_path = common.prep_rdoinfo_test(tmpdir, 'sample-1')
    rv = release(local_info=rdoinfo_path, repo='')
    cap = capsys.readouterr()
    output = cap.out
    assert "zed" in output
    assert "yoga" in output
    assert "xena" in output
    assert "wallaby" in output
    assert "victoria" in output
    assert "ussuri" in output
