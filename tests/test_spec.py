# coding=utf-8
from rdopkg import exception
from rdopkg.utils import specfile
import pytest

import test_common as common


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


def _assert_vr(vr, epoch_arg, result):
    epoch, version, release = vr

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
        return "MOCKED-OUT-VR"

    def _expand_macro(macro):
        return macro

    spec = specfile.Spec()
    spec.get_tag = _get_tag_mock
    spec.expand_macro = _expand_macro
    vr = spec.get_vr(epoch=epoch_arg)
    assert vr == result


def test_get_vr():
    _assert_vr((None, '1.2.3', '0.1'), None, '1.2.3-0.1')
    _assert_vr((None, '1.2.3', '666%{?dist}'), False, '1.2.3-666')
    _assert_vr((None, '1.2.3', ''), True, '0:1.2.3')
    _assert_vr((23, '1.2.3', ''), None, '23:1.2.3')
    _assert_vr((23, '1.2.3', '0.1'), False, '1.2.3-0.1')
    _assert_vr((23, '1.2.3', '666%{?dist}'), True, '23:1.2.3-666')


def test_patches_base_add_patched(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        ver, np = spec.get_patches_base()
        assert ver is None
        assert np == 0
        spec.set_patches_base('+2')
        spec.save()
    common.assert_distgit(dist_path, 'patched-ex')


def test_patches_base_add_empty(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        ver, np = spec.get_patches_base()
        assert ver is None
        assert np == 0
        spec.set_patches_base_version('+2')
        spec.save()
    common.assert_distgit(dist_path, 'empty-ex')


def test_patches_base_noop_weird(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty-weird')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        ver, np = spec.get_patches_base()
        assert ver == 'banana'
        assert np == 2
        spec.set_patches_base_version('banana')
        spec.save()
    common.assert_distgit(dist_path, 'empty-weird')


def test_set_commit_ref_macro(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'commit')
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
    dist_path = common.prep_spec_test(tmpdir, 'magic-comments')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        assert spec.get_patches_ignore_regex().pattern == 'DROP-IN-RPM'
        assert spec.get_patches_base() == ('1.2.3', 0)


def test_new_version_patches_base_ignore_new_version(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'magic-comments')
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
    dist_path = common.prep_spec_test(tmpdir, 'magic-comments')
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


def test_set_patches_base_case_1_minimal():
    spec = specfile.Spec(txt='foo\n# patches_base=1.2.3\nbaz\n')
    spec.set_patches_base_version(None)
    assert spec.txt == 'foo\nbaz\n'


def test_set_patches_base_case_1_a_minimal():
    spec = specfile.Spec(txt='foo\n#patches_base=1.2.3\nbaz\n')
    spec.set_patches_base_version(None)
    assert spec.txt == 'foo\nbaz\n'


# make sure dropping patches_base with following # is clean
def test_set_patches_base_case_2_minimal():
    spec = specfile.Spec(txt='foo\n# patches_base=1.2.3\n#\nbaz\n')
    spec.set_patches_base_version(None)
    assert spec.txt == 'foo\nbaz\n'


# found bug where following comment mangles prior line when clearing
# patches_base
def test_set_patches_base_case_3_minimal():
    spec = specfile.Spec(txt='foo\n# patches_base=1.2.3\n# bar\nbaz\n')
    spec.set_patches_base_version(None)
    assert 'foo\n' in spec.txt
    assert 'patches_base' not in spec.txt
    assert 'baz\n' in spec.txt


# make sure multiple whitespace leaves Version line intact (workaround)
def test_set_patches_base_case_4_minimal():
    spec = specfile.Spec(txt='foo\n\n# patches_base=1.2.3\n# bar\nbaz\n')
    spec.set_patches_base_version(None)
    assert 'foo\n' in spec.txt
    assert 'patches_base' not in spec.txt
    assert 'baz\n' in spec.txt


# Eat Trailing #\n comments
def test_set_patches_base_case_5_minimal():
    spec = specfile.Spec(txt='foo\n\n# patches_base=1.2.3\n#\n#\nbaz\n')
    spec.set_patches_base_version(None)
    assert 'foo\n' in spec.txt
    assert '^#\n' not in spec.txt
    assert 'baz\n' in spec.txt


# patches_base/patches_ignore
def test_set_patches_base_case_6_minimal():
    spec = specfile.Spec(txt='Version: 1.2.3\n\n# patches_base=1.2.3\n# patches_ignore=DROP-IN-RPM\n#\nPatch0=foo.patch\n')  # noqa
    spec.set_patches_base_version(None)
    assert 'Version: 1.2.3\n' in spec.txt
    assert '# patches_ignore=DROP-IN-RPM\n' in spec.txt
    assert 'Patch0=foo.patch\n' in spec.txt


# patches_ignore/patches_base
def test_set_patches_base_case_7_minimal():
    spec = specfile.Spec(txt='Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=1.2.3\n#\nPatch0=foo.patch\n')  # noqa
    spec.set_patches_base_version(None)
    assert 'Version: 1.2.3\n' in spec.txt
    assert '# patches_ignore=DROP-IN-RPM\n' in spec.txt
    assert 'Patch0=foo.patch\n' in spec.txt


# patches_ignore/patches_base keep patches_base
def test_set_patches_base_case_8_minimal():
    spec = specfile.Spec(txt='Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=\n#\nPatch0=foo.patch\n')  # noqa
    spec.set_patches_base_version(None)
    assert '# patches_ignore=DROP-IN-RPM\n' in spec.txt
    assert '# patches_base=1.2.3\n' in spec.txt
    assert '# patches_ignore=DROP-IN-RPM\n' in spec.txt


def test_get_magic_comment(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'patched-filter')
    with dist_path.as_cwd():
        spec = specfile.Spec()

        def _assert_mc(name, exp_val):
            spec_val = spec.get_magic_comment(name)
            assert spec_val == exp_val

        _assert_mc('patches_base', '+2')
        _assert_mc('patches_ignore', 'DROP-IN-RPM')
        _assert_mc('not_really_there', None)
        _assert_mc('¯\_(ツ)_/¯', None)


def test_get_magic_comment_minimal_1():
    spec = specfile.Spec(txt='\n')
    assert spec.get_magic_comment('foo') is None


def test_get_magic_comment_minimal_2():
    spec = specfile.Spec(txt='# foo=1\n')
    assert '1' == spec.get_magic_comment('foo')


def test_get_magic_comment_minimal_2a():
    spec = specfile.Spec(txt='#foo=1 \n')
    assert '1' == spec.get_magic_comment('foo')


def test_get_magic_comment_minimal_2b():
    spec = specfile.Spec(txt='#     foo = 1\n')
    assert '1' == spec.get_magic_comment('foo')


def test_get_magic_comment_minimal_3():
    spec = specfile.Spec(txt='# foo\n')
    assert spec.get_magic_comment('foo') is None


def test_get_magic_comment_minimal_4():
    spec = specfile.Spec(txt='# foo=1\n# bar=baz\n')
    assert 'baz' == spec.get_magic_comment('bar')


def test_get_magic_comment_minimal_5():
    spec = specfile.Spec(txt='#\n#\n# foo=1\n#\n# bar=baz\n#\n\n')
    assert 'baz' == spec.get_magic_comment('bar')


def test_get_magic_comment_minimal_6():
    spec = specfile.Spec(txt='  # foo=1\n')
    assert spec.get_magic_comment('foo') is None


@pytest.mark.skip(
    'Ignoring eged case until we get more details for expected behavior')
def test_get_magic_comment_minimal_7():
    spec = specfile.Spec(txt='# foo=\n')
    assert '' == spec.get_magic_comment('foo')


def test_get_last_changelog_entry_0():
    txt = 'Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=1.2.3\n#\nPatch0=foo.patch\n'  # noqa
    spec = specfile.Spec(txt=txt)
    r = spec.get_last_changelog_entry()
    assert ('', []) == r


def test_get_last_changelog_entry_1():
    txt = 'Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=1.2.3\n#\nPatch0=foo.patch\n'  # noqa
    spec = specfile.Spec(txt=txt + '%changelog\nfoo')
    r = spec.get_last_changelog_entry()
    assert ('foo', []) == r


def test_get_last_changelog_entry_1_case_insensitive():
    txt = 'Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=1.2.3\n#\nPatch0=foo.patch\n'  # noqa
    spec = specfile.Spec(txt=txt + '%ChangeLog\nfoo')
    r = spec.get_last_changelog_entry()
    assert ('foo', []) == r


def test_get_last_changelog_entry_multiple_sections():
    with pytest.raises(exception.MultipleChangelog):
        txt = 'Version: 1.2.3\n\n'
        spec = specfile.Spec(txt=txt + '%changelog\n* 2017-01-01\n- foo1\n\n%changelog\nbar\n')  # noqa
        r = spec.get_last_changelog_entry()
        assert False, r
