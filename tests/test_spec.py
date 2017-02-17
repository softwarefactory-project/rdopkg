from rdopkg import exception
from rdopkg.utils import specfile

import common


def _assert_vparts(version, numeric, rest):
    parts = specfile.version_parts(version)
    assert parts == (numeric, rest)


def test_version_parts():
    _assert_vparts('', '', '')
    _assert_vparts('1', '1', '')
    _assert_vparts('1.2.3', '1.2.3', '')
    _assert_vparts('1.2.3.0b1', '1.2.3', '.0b1')
    _assert_vparts('10.10.10.0rc2', '10.10.10', '.0rc2')
    _assert_vparts('a', 'a', '')
    _assert_vparts('a.b', 'a.b', '')
    _assert_vparts('1.b42', '1', '.b42')
    _assert_vparts('1.0.b4.2', '1.0', '.b4.2')
    _assert_vparts('1.2.3.a.b-c.d', '1.2.3', '.a.b-c.d')


def _assert_rparts(release, nums, milestone, macros):
    parts = specfile.release_parts(release)
    assert parts == (nums, milestone, macros)


def test_release_parts():
    _assert_rparts('1', '1', '', '')
    _assert_rparts('0.1.2', '0.1.2', '', '')
    _assert_rparts('1.b1', '1', '.b1', '')
    _assert_rparts('0.1.rc2', '0.1', '.rc2', '')
    _assert_rparts('0.1%{?dist}', '0.1', '', '%{?dist}')
    _assert_rparts('0.1.b1%{?dist}', '0.1', '.b1', '%{?dist}')
    _assert_rparts('0.1.b1.%{?dist}', '0.1', '.b1', '.%{?dist}')
    _assert_rparts('0.1%{m1}%{m2}', '0.1', '', '%{m1}%{m2}')
    _assert_rparts('0.1.%m1%m2', '0.1', '', '.%m1%m2')
    _assert_rparts('0.1.0rc1%{m}', '0.1', '.0rc1', '%{m}')
    _assert_rparts('0.1.0.0b2%m', '0.1.0', '.0b2', '%m')
    _assert_rparts('0.1.0.000a000', '0.1.0', '.000a000', '')
    _assert_rparts('10.10.10.%{?milestone}', '10.10.10', '.%{?milestone}', '')
    _assert_rparts('10.10.10.%{?milestone}%{foo}',
                   '10.10.10', '.%{?milestone}', '%{foo}')
    _assert_rparts('0.0.0%{?milestone}.%bar',
                   '0.0.0', '%{?milestone}', '.%bar')
    _assert_rparts('%{ver}', '', '', '%{ver}')


def _assert_nvr(nvr, epoch_arg, result):
    epoch, version, release = nvr

    def _get_tag_mock(tag, default=None, expand_macros=False):
        if tag == 'Version':
            return version
        elif tag == 'Release':
            return release
        elif tag == 'Epoch':
            if epoch:
                return epoch
            raise exception.SpecFileParseError(
                spec_fn='TESTING', error='Pretending Epoch tag not found')
        return "MOCKED-OUT-NVR"

    spec = specfile.Spec()
    spec.get_tag = _get_tag_mock
    nvr = spec.get_nvr(epoch=epoch_arg)
    assert nvr == result


def test_get_nvr():
    _assert_nvr((None, '1.2.3', '0.1'),         None,  '1.2.3-0.1')
    _assert_nvr((None, '1.2.3', '666%{?dist}'), False, '1.2.3-666')
    _assert_nvr((None, '1.2.3', ''),            True,  '0:1.2.3')
    _assert_nvr((23, '1.2.3', ''),              None,  '23:1.2.3')
    _assert_nvr((23, '1.2.3', '0.1'),           False, '1.2.3-0.1')
    _assert_nvr((23, '1.2.3', '666%{?dist}'),   True,  '23:1.2.3-666')


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


def test_set_commit_ref_macro(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'commit')
    spec_path = dist_path.join('foo.spec')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        spec.set_commit_ref_macro('86a713c35718520cb3b681260182a8388ac809f3')
        spec.save()
    common.assert_distgit(dist_path, 'commit-patched')


def test_get_patches_ignore_regex(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-ex-filter')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        regex = spec.get_patches_ignore_regex()
        assert regex.pattern == 'DROP-IN-RPM'


def test_get_patches_ignore_regex_fail(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-filter-bogus')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        regex = spec.get_patches_ignore_regex()
        assert regex is None


def test_new_version_patches_base_ignore_load(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'upgrade_patches_ignore_base')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        assert spec.get_patches_ignore_regex().pattern == 'DROP-IN-RPM'
        assert spec.get_patches_base() == ('1.2.3', 0)


def test_new_version_patches_base_ignore_new_version(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'upgrade_patches_ignore_base')
    with dist_path.as_cwd():
        spec2 = specfile.Spec()
        spec2.set_tag('Version', '1.2.4')
        spec2.set_release('1')
        spec2.set_patches_base_version(None)
        spec2.save()
        spec2 = None
        spec = specfile.Spec()
        assert spec.get_patches_ignore_regex().pattern == 'DROP-IN-RPM'


def test_new_version_patches_base_ignore_mangling_minimal(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'upgrade_patches_ignore_base')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        spec.set_patches_base_version(None)
        assert spec.get_patches_ignore_regex().pattern == 'DROP-IN-RPM'


def test_new_version_patches_base_ignore_mangling_minimal_2(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched-filter')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        spec.set_patches_base_version(None)
        assert spec.get_patches_ignore_regex().pattern == 'DROP-IN-RPM'
