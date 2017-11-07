from rdopkg.cli import rdopkg
from rdopkg.utils.git import git
from rdopkg.utils import log

import test_common as common
from test_common import DIST_POSTFIX
import pytest

RPM_AVAILABLE = False
try:
    import rpm  # NOQA
    RPM_AVAILABLE = True
except ImportError:
    pass


def _test_new_version(asset, dir, steps):
    dist_path = common.prep_spec_test(dir, asset)
    log.log.setLevel(log.WARN)

    with dist_path.as_cwd():
        common.prep_patches_branch()
        for new_version, spec_version, spec_release_parts, spec_milestone \
                in steps:
            commit_before = git('rev-parse', 'HEAD')
            common.add_patches(tag=new_version)
            rdopkg('new-version', '-l', '-d', new_version)

            # after
            commit_after = git('rev-parse', 'HEAD')
            common.assert_spec_version(spec_version, spec_release_parts,
                                       spec_milestone)
            assert commit_before != commit_after


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_new_version_basic(tmpdir):
    steps = [
        ('3.4.5', '3.4.5', ('1', '', DIST_POSTFIX), None),
        ('123.456.789.000', '123.456.789.000', ('1', '', DIST_POSTFIX), None),
    ]
    _test_new_version('some', tmpdir, steps)


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_new_version_milestone(tmpdir):
    steps = [
        ('3.4.5', '3.4.5', ('1', '', DIST_POSTFIX), None),
        ('4.0.0.0b1',
         '4.0.0', ('0.1', '%{?milestone}', DIST_POSTFIX), '.0b1'),
        ('4.0.0.0rc1',
         '4.0.0', ('0.2', '%{?milestone}', DIST_POSTFIX), '.0rc1'),
        ('4.0.0', '4.0.0', ('1', '', DIST_POSTFIX), None),
    ]
    _test_new_version('some', tmpdir, steps)
