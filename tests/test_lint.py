import pytest
import subprocess

from rdopkg.cli import rdopkg

import test_common as common


RPMLINT_AVAILABLE = False
try:
    subprocess.call(["rpmlint", "--version"])
    RPMLINT_AVAILABLE = True
except Exception as e:
    pass


def _assert_sanity_out(o):
    assert 'ERRORS found:' in o
    assert 'E: buildarch-before-sources' in o


def _assert_rpmlint_out(o):
    # check expected errors were raised
    assert 'ERRORS found:' in o
    assert 'E: hardcoded-library-path' in o
    assert 'E: specfile-error warning:' in o
    assert 'prereq is deprecated: PreReq' in o
    # check expected warnings were raised
    assert 'WARNINGS found:' in o
    assert 'W: macro-in-%changelog' in o
    assert 'W: setup-not-in-prep' in o
    # make sure parsing rpmlint output was a success
    assert 'Failed to parse rpmlint output' not in o


def test_lint_sanity(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'lint')
    rv = -1
    with dist_path.as_cwd():
        rv = rdopkg('lint', '--lint-checks', 'sanity')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert rv == 23


@pytest.mark.skipif('RPMLINT_AVAILABLE == False')
def test_lint_rpmlint(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'lint')
    rv = -1
    with dist_path.as_cwd():
        rv = rdopkg('lint', '--lint-checks', 'rpmlint')
    cap = capsys.readouterr()
    o = cap.out
    _assert_rpmlint_out(o)
    assert rv == 23


@pytest.mark.skipif('RPMLINT_AVAILABLE == False')
def test_lint_all(tmpdir, capsys):
    # run `rdopkg lint` on tests/assets/spec/lint.spec
    dist_path = common.prep_spec_test(tmpdir, 'lint')
    rv = -1
    with dist_path.as_cwd():
        rv = rdopkg('lint')
    cap = capsys.readouterr()
    o = cap.out
    _assert_rpmlint_out(o)
    _assert_sanity_out(o)
    # linting problems are indicated by exit code 23
    assert rv == 23
