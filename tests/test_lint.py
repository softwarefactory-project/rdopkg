import pytest
import subprocess

from rdopkg.cli import rdopkg

import test_common as common


RPMLINT_AVAILABLE = False
RPMLINT_VERSION = (0, 0, 0)
try:
    RPMLINT_VERSION = subprocess.run(["/usr/bin/rpmlint", "--version"],
                                     capture_output=True,
                                     text=True)
    RPMLINT_VERSION = RPMLINT_VERSION.stdout.replace("rpmlint version ", "")
    RPMLINT_VERSION = tuple(map(int, RPMLINT_VERSION.split('.')))
    RPMLINT_AVAILABLE = True
except Exception as e:
    pass


def _assert_sanity_out(o):
    # make sure parsing rpmlint output was a success
    assert 'Failed to parse rpmlint output' not in o
    assert 'ERRORS found:' in o
    assert 'E: buildarch-before-sources' in o


def _assert_rpmlint_out(o):
    # check expected errors were raised
    assert 'ERRORS found:' in o
    assert 'E: specfile-error' in o
    # make sure parsing rpmlint output was a success
    assert 'Failed to parse rpmlint output' not in o
    # check expected warnings were raised
    assert 'WARNINGS found:' in o
    assert 'W: macro-in-%changelog' in o
    assert 'W: setup-not-in-prep' in o


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
@pytest.mark.skipif('RPMLINT_VERSION < (2, 0, 0)')
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
@pytest.mark.skipif('RPMLINT_VERSION < (2, 0, 0)')
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
