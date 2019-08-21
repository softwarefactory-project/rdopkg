# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from rdopkg.cli import rdopkg
from rdopkg.utils.git import git, git_branch
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


def _test_patch(asset, version, dir):
    dist_path = common.prep_spec_test(dir, asset)
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
        assert commit_before != commit_after, "No commit created"
        prev = git('rev-parse', 'HEAD~')
        assert prev == commit_before, "Multiple commits created"


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_milestone(tmpdir):
    _test_patch('milestone', ('1.2.3', ('0.4', '%{?milestone}',
                DIST_POSTFIX), '.0rc2'), tmpdir)


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_milestone_bug(tmpdir):
    # make sure rdopkg removes unwanted '%global milestone %{?milestone}'
    _test_patch('milestone-bug',
                ('1.2.3', ('0.4', '', DIST_POSTFIX), None),
                tmpdir)


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_remove(tmpdir):

    dist_path = common.prep_spec_test(tmpdir, 'patched')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches()
        commit_before = git('rev-parse', 'HEAD')
        common.remove_patches(1)
        rdopkg('patch', '-l')
        commit_after = git('rev-parse', 'HEAD')
        git_clean = git.is_clean()
        common.norm_changelog()
    common.assert_distgit(dist_path, 'patch-remove')
    assert commit_before != commit_after, "New commit not created"
    assert git_clean, "git not clean after action"


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_add(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches()
        commit_before = git('rev-parse', 'HEAD')
        common.add_n_patches(3)
        rdopkg('patch', '-l')
        commit_after = git('rev-parse', 'HEAD')
        git_clean = git.is_clean()
        common.norm_changelog()
    common.assert_distgit(dist_path, 'patch-add')
    assert commit_before != commit_after, "New commit not created"
    assert git_clean, "git not clean after action"


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_mix(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched')
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches()
        commit_before = git('rev-parse', 'HEAD')
        common.remove_patches(1)
        common.add_n_patches(3)
        rdopkg('patch', '-l')
        commit_after = git('rev-parse', 'HEAD')
        git_clean = git.is_clean()
        common.norm_changelog()
    common.assert_distgit(dist_path, 'patch-mix')
    assert commit_before != commit_after, "New commit not created"
    assert git_clean, "git not clean after action"


def _test_patch_noop(tmpdir, distgit, cmd):
    dist_path = common.prep_spec_test(tmpdir, distgit)
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches()
        # regen patch files in order for hashes to match git
        rdopkg('update-patches', '--amend')
        commit_before = git('rev-parse', 'HEAD')
        rdopkg(*cmd)
        commit_after = git('rev-parse', 'HEAD')
        git_clean = git.is_clean()
    common.assert_distgit(dist_path, distgit)
    assert commit_before == commit_after, "New commit created for noop"
    assert git_clean, "git not clean after action"


def test_patch_noop(tmpdir):
    _test_patch_noop(tmpdir, 'patched', ['patch', '-l'])


def test_patch_noop_detect(tmpdir):
    _test_patch_noop(tmpdir,
                     'patched', ['patch', '-l', '--changelog', 'detect'])


def test_patch_noop_count(tmpdir):
    _test_patch_noop(tmpdir,
                     'patched', ['patch', '-l', '--changelog', 'count'])


def test_patch_noop_plain(tmpdir):
    _test_patch_noop(tmpdir, 'patched', ['patch', '-l', '-C', 'plain'])


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_noop_no_bump(tmpdir):
    _test_patch_noop(tmpdir, 'patched', ['patch', '-l', '--no-bump'])


def _test_patch_regen(tmpdir, distgit, distgit_after,
                      cmd, norm_changelog=True):
    dist_path = common.prep_spec_test(tmpdir, distgit)
    with dist_path.as_cwd():
        common.prep_patches_branch()
        common.add_patches()
        commit_before = git('rev-parse', 'HEAD')
        rdopkg(*cmd)
        commit_after = git('rev-parse', 'HEAD')
        git_clean = git.is_clean()
        if norm_changelog:
            common.norm_changelog()
    common.assert_distgit(dist_path, distgit_after)
    assert commit_before != commit_after, \
        "New commit not created after patch regen"
    assert git_clean, "git not clean after action"


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_regen(tmpdir):
    _test_patch_regen(tmpdir, 'patched', 'patched-regen', ['patch', '-l'])


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_regen_detect(tmpdir):
    _test_patch_regen(tmpdir, 'patched', 'patched-regen',
                      ['patch', '-l', '-C', 'detect'])


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_regen_count(tmpdir):
    _test_patch_regen(tmpdir, 'patched', 'patched-regen',
                      ['patch', '-l', '-C', 'count'])


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_regen_plain(tmpdir):
    _test_patch_regen(tmpdir, 'patched', 'patched-regen',
                      ['patch', '-l', '--changelog', 'plain'])


def test_patch_regen_no_bump(tmpdir):
    _test_patch_regen(tmpdir, 'patched', 'patched',
                      ['patch', '-l', '--no-bump'], norm_changelog=False)


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_patch_unicode(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched')
    with dist_path.as_cwd():
        git('config', 'user.name', 'Přikrášlený Žluťoučký Kůň')
        common.prep_patches_branch()
        common.add_patches()
        commit_before = git('rev-parse', 'HEAD')
        with git_branch('master-patches'):
            common.do_patch('foofile', '#to chceš',
                            "Přikrášlený Žluťoučký Kůň")
            common.do_patch('foofile', '#to asi chceš', "Přikrášlení koně")
            common.do_patch('foofile', '#to nechceš', "ěščřžýáí")
        rdopkg('patch', '-l')
        commit_after = git('rev-parse', 'HEAD')
        git_clean = git.is_clean()
    assert commit_before != commit_after, "New commit not created"
    assert git_clean, "git not clean after action"
