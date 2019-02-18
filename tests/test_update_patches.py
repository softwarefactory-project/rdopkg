import shutil
import pytest

from rdopkg.actions.distgit.actions import update_patches
from rdopkg.utils.git import git
from rdopkg.utils import specfile
import rdopkg.exception

import test_common as common


def test_update_empty(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        spec_before = spec_path.read()
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        spec_after = spec_path.read()
    assert spec_after == spec_before
    with dist_path.as_cwd():
        common.add_patches()
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        spec_after = spec_path.read()
    common.assert_distgit(dist_path, 'patched')


def test_update_noop(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        spec_before = spec_path.read()
        common.add_patches()
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        spec_after = spec_path.read()
        assert spec_after == spec_before
        spec_before = spec_after
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        spec_after = spec_path.read()
        assert spec_after == spec_before


def test_update_full(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'some-ex')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
    common.assert_distgit(dist_path, 'patched-ex')


def test_update_weird(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-weird')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
    common.assert_distgit(dist_path, 'patched-weird')


def test_update_dense(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-dense')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
    common.assert_distgit(dist_path, 'patched-dense')


def test_update_dense_ex(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-dense-ex')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
    common.assert_distgit(dist_path, 'patched-dense-ex')


def test_update_comments(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'some-comments')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
    common.assert_distgit(dist_path, 'patched-comments')


def test_update_git_am(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'git-am')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        apply_method = specfile.Spec().patches_apply_method()
    assert apply_method == 'git-am'
    common.assert_distgit(dist_path, 'patched-git-am')


def test_update_git_am_buildarch_fail(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'git-am-fail')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        with pytest.raises(rdopkg.exception.LintProblemsFound):
            update_patches('master',
                           local_patches_branch='master-patches',
                           version='1.2.3')
        apply_method = specfile.Spec().patches_apply_method()
    assert apply_method == 'git-am'


def test_update_autosetup(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'autosetup')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        apply_method = specfile.Spec().patches_apply_method()
    assert apply_method == 'autosetup'
    common.assert_distgit(dist_path, 'patched-autosetup')


def test_wipe(tmpdir):
    shutil.copyfile(common.spec_path('some'), str(tmpdir.join('foo.spec')))
    with tmpdir.as_cwd():
        spec = specfile.Spec()
        spec.wipe_patches()
        spec.save()
        with open('foo.spec', 'r') as fp:
            spec_after = fp.read()
    with open(common.spec_path('empty'), 'r') as fp:
        spec_exp = fp.read()
    assert spec_after == spec_exp
    # second wipe must be a no-op
    with tmpdir.as_cwd():
        spec = specfile.Spec()
        spec.wipe_patches()
        spec.save()
        with open('foo.spec', 'r') as fp:
            spec_after = fp.read()
    assert spec_after == spec_exp


def test_filter_out(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-ex-filter')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches(extra=True, filtered=True)
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
    common.assert_distgit(dist_path, 'patched-filter')


def test_update_milestone(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'milestone')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        spec_before = spec_path.read()
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        spec_after = spec_path.read()
    assert spec_after == spec_before
    with dist_path.as_cwd():
        common.add_patches()
        update_patches('master',
                       local_patches_branch='master-patches',
                       version='1.2.3')
        spec_after = spec_path.read()
    common.assert_distgit(dist_path, 'patched-milestone')


def test_update_double_patches_base(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'double-patches')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        with pytest.raises(rdopkg.exception.LintProblemsFound):
            update_patches('master',
                           local_patches_branch='master-patches',
                           version='1.2.3')
    common.assert_distgit(dist_path, 'double-patches')
