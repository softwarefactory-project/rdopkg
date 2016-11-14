from rdopkg.cli import rdopkg
from rdopkg.utils.cmd import git
from rdopkg.utils import log

import common
from common import DIST_POSTFIX


def _test_patch(asset, version, dir):
    dist_path = common.prep_spec_test(dir, asset)
    spec_path = dist_path.join('foo.spec')
    log.log.setLevel(log.WARN)

    with dist_path.as_cwd():
        spec_version, spec_release_parts, spec_milestone = version
        tag = spec_version
        if spec_milestone:
            tag += spec_milestone

        common.prep_patches_branch(tag=tag)
        commit_before = git('rev-parse', 'HEAD')
        common.add_patches()

        rdopkg('patch', '-l')
        # after
        commit_after = git('rev-parse', 'HEAD')

        common.assert_spec_version(spec_version, spec_release_parts,
                                   spec_milestone)
        assert commit_before != commit_after


def test_patch_milestone(tmpdir):
    _test_patch('milestone', ('1.2.3', ('0.4', '%{?milestone}', DIST_POSTFIX), '.0rc2'), tmpdir)


def test_patch_milestone_bug(tmpdir):
    # make sure rdopkg removes unwanted '%global milestone %{?milestone}'
    _test_patch('milestone-bug', ('1.2.3', ('0.4', '', DIST_POSTFIX), None), tmpdir)

