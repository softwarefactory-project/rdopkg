from rdopkg import actions
from rdopkg.utils import specfile
from rdopkg.utils.cmd import git, run

import common


def _assert_vparts(version, numeric, rest):
    parts = specfile.version_parts(version)
    assert parts == (numeric, rest)


def test_version_parts():
    _assert_vparts('', '', None)
    _assert_vparts('1', '1', None)
    _assert_vparts('1.2.3', '1.2.3', None)
    _assert_vparts('a', 'a', None)
    _assert_vparts('a.b', 'a.b', None)
    _assert_vparts('1.b42', '1', 'b42')
    _assert_vparts('1.0.b4.2', '1.0', 'b4.2')
    _assert_vparts('1.2.3.a.b-c.d', '1.2.3', 'a.b-c.d')


def _assert_rparts(release, nums, milestone, macros):
    parts = specfile.release_parts(release)
    assert parts == (nums, milestone, macros)


def test_release_parts():
    _assert_rparts('1', '1', '', '')
    _assert_rparts('0.1.2', '0.1.2', '', '')
    _assert_rparts('1.b1', '1.', 'b1', '')
    _assert_rparts('0.1.rc2', '0.1.', 'rc2', '')
    _assert_rparts('0.1%{?dist}', '0.1', '', '%{?dist}')
    _assert_rparts('0.1.b1%{?dist}', '0.1.', 'b1', '%{?dist}')
    _assert_rparts('0.1.b1.%{?dist}', '0.1.', 'b1.', '%{?dist}')
    _assert_rparts('0.1%{m1}%{m2}', '0.1', '', '%{m1}%{m2}')
    _assert_rparts('0.1.%{m1}%{m2}', '0.1.', '', '%{m1}%{m2}')
    _assert_rparts('%{ver}', '', '', '%{ver}')


def test_patches_base_add_patched(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        spec_before = spec_path.read()
        spec = specfile.Spec()
        ver, np = spec.get_patches_base()
        assert ver is None
        assert np == 0
        spec.set_patches_base('+2')
        spec.save()
        spec_after = spec_path.read()
    common.assert_distgit(dist_path, 'patched-ex')


def test_patches_base_add_empty(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        spec_before = spec_path.read()
        spec = specfile.Spec()
        ver, np = spec.get_patches_base()
        assert ver is None
        assert np == 0
        spec.set_patches_base_version('+2')
        spec.save()
        spec_after = spec_path.read()
    common.assert_distgit(dist_path, 'empty-ex')


def test_patches_base_noop_weird(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-weird')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        spec_before = spec_path.read()
        spec = specfile.Spec()
        ver, np = spec.get_patches_base()
        assert ver == 'banana'
        assert np == 2
        spec.set_patches_base_version('banana')
        spec.save()
        spec_after = spec_path.read()
    common.assert_distgit(dist_path, 'empty-weird')
