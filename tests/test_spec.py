# coding=utf-8
from __future__ import unicode_literals

from rdopkg import exception
from rdopkg.utils import specfile
from collections import defaultdict
import pytest

import test_common as common

RPM_AVAILABLE = False
try:
    import rpm  # NOQA
    RPM_AVAILABLE = True
except ImportError:
    pass


@pytest.mark.parametrize('version,numeric,rest', [
    ('', '', ''),
    ('1', '1', ''),
    ('1.2.3', '1.2.3', ''),
    ('1.2.3.0b1', '1.2.3', '.0b1'),
    ('10.10.10.0rc2', '10.10.10', '.0rc2'),
    ('a', 'a', ''),
    ('a.b', 'a.b', ''),
    ('1.b42', '1', '.b42'),
    ('1.0.b4.2', '1.0', '.b4.2'),
    ('1.2.3.a.b-c.d', '1.2.3', '.a.b-c.d'),
])
def test_version_parts(version, numeric, rest):
    parts = specfile.version_parts(version)
    assert parts == (numeric, rest)


@pytest.mark.parametrize('release,nums,milestone,macros', [
    ('1', '1', '', ''),
    ('0.1.2', '0.1.2', '', ''),
    ('1.b1', '1', '.b1', ''),
    ('0.1.rc2', '0.1', '.rc2', ''),
    ('0.1%{?dist}', '0.1', '', '%{?dist}'),
    ('0.1.b1%{?dist}', '0.1', '.b1', '%{?dist}'),
    ('0.1.b1.%{?dist}', '0.1', '.b1', '.%{?dist}'),
    ('0.1%{m1}%{m2}', '0.1', '', '%{m1}%{m2}'),
    ('0.1.%m1%m2', '0.1', '', '.%m1%m2'),
    ('0.1.0rc1%{m}', '0.1', '.0rc1', '%{m}'),
    ('0.1.0.0b2%m', '0.1.0', '.0b2', '%m'),
    ('0.1.0.000a000', '0.1.0', '.000a000', ''),
    ('10.10.10.%{?milestone}', '10.10.10', '.%{?milestone}', ''),
    ('10.10.10.%{?milestone}%{foo}',
     '10.10.10', '.%{?milestone}', '%{foo}'),
    ('0.0.0%{?milestone}.%bar',
     '0.0.0', '%{?milestone}', '.%bar'),
    ('%{ver}', '', '', '%{ver}'),
])
def test_release_parts(release, nums, milestone, macros):
    parts = specfile.release_parts(release)
    assert parts == (nums, milestone, macros)


@pytest.mark.parametrize('vr,epoch_arg,result', [
    ((None, '1.2.3', '0.1'), None, '1.2.3-0.1'),
    ((None, '1.2.3', '666%{?dist}'), False, '1.2.3-666'),
    ((None, '1.2.3', ''), True, '0:1.2.3'),
    ((23, '1.2.3', ''), None, '23:1.2.3'),
    ((23, '1.2.3', '0.1'), False, '1.2.3-0.1'),
    ((23, '1.2.3', '666%{?dist}'), True, '23:1.2.3-666'),
])
def test_get_vr(vr, epoch_arg, result):
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


@pytest.mark.skipif('RPM_AVAILABLE == False')
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


@pytest.mark.skipif('RPM_AVAILABLE == False')
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


def test_set_magic_comments_base_case_8_a_minimal():
    spec = specfile.Spec(txt='Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=\n#\nPatch0=foo.patch\n')  # noqa
    spec.set_magic_comment('patches_base', '1.2.3')
    assert '# patches_ignore=DROP-IN-RPM\n' in spec.txt
    assert '# patches_base=1.2.3\n' in spec.txt


def test_set_magic_comments_base_case_9_minimal():
    spec = specfile.Spec(txt='Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n# patches_base=\n# patches_base=foo\n#\nPatch0=foo.patch\n')  # noqa
    spec.set_magic_comment('patches_base', '1.2.3')
    assert '# patches_ignore=DROP-IN-RPM\n' in spec.txt
    assert '# patches_base=1.2.3\n' in spec.txt


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
    txt = 'Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n' + \
          '# patches_base=1.2.3\n#\nPatch0=foo.patch\n'
    spec = specfile.Spec(txt=txt)
    r = spec.get_last_changelog_entry()
    assert ('', []) == r


def test_get_last_changelog_entry_1():
    txt = 'Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n' + \
          '# patches_base=1.2.3\n#\nPatch0=foo.patch\n'
    spec = specfile.Spec(txt=txt + '%changelog\nfoo')
    r = spec.get_last_changelog_entry()
    assert ('foo', []) == r


def test_get_last_changelog_entry_1_case_insensitive():
    txt = 'Version: 1.2.3\n\n# patches_ignore=DROP-IN-RPM\n' + \
          '# patches_base=1.2.3\n#\nPatch0=foo.patch\n'
    spec = specfile.Spec(txt=txt + '%ChangeLog\nfoo')
    r = spec.get_last_changelog_entry()
    assert ('foo', []) == r


def test_get_last_changelog_entry_multiple_sections():
    with pytest.raises(exception.MultipleChangelog):
        txt = 'Version: 1.2.3\n\n'
        spec = specfile.Spec(txt=txt + '%changelog\n* 2017-01-01\n'
                             + '- foo1\n\n%changelog\nbar\n')
        r = spec.get_last_changelog_entry()
        assert False, r


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_get_source_urls(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        urls = spec.get_source_urls()
    assert urls == ['http://pypi.python.org/packages/source/f/foo/foo-1.2.3.tar.gz']  # noqa


@pytest.mark.skipif('RPM_AVAILABLE == False')
def test_get_source_fns(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'empty')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        fns = spec.get_source_fns()
    assert fns == ['foo-1.2.3.tar.gz']


def test_set_magic_modify():
    txt = ('Version: 1.2.3\n\nSource0: test.tar.gz\n# patches_ignore='
           'DROP-IN-RPM\n# patches_base=1.2.3\n#\nPatch0=foo.patch\n')
    spec = specfile.Spec(txt=txt + '%changelog\nfoo')
    spec.set_magic_comment('patches_ignore', 'foo')
    assert 'test.tar.gz\n' in spec.txt
    assert '# patches_ignore=foo\n' in spec.txt
    assert '# patches_ignore=DROP-IN-RPM\n' not in spec.txt


def test_set_magic_create():
    txt = ('Version: 1.2.3\n\nSource0: test.tar.gz\n# patches_ignore='
           'DROP-IN-RPM\n# patches_base=1.2.3\n#\nPatch0=foo.patch\n')
    spec = specfile.Spec(txt=txt + '%changelog\nfoo')
    spec.set_magic_comment('new_magic_comment', 'foo')
    assert 'test.tar.gz\n' in spec.txt
    assert '# new_magic_comment=foo\n' in spec.txt


def test_set_magic_modify_once():
    txt = ('Version: 1.2.3\n\nSource0: test.tar.gz\n# my_comment=abc\n'
           '# my_comment=1.2.3\n')
    spec = specfile.Spec(txt=txt + '%changelog\nfoo')
    spec._fn = 'foo.spec'
    spec.set_magic_comment('my_comment', 'foo')
    assert '# my_comment=foo\n' in spec.txt
    assert '# my_comment=abc\n' not in spec.txt
    assert '# my_comment=1.2.3\n' not in spec.txt


def test_set_magic_comment_only_patches_base():
    spec = specfile.Spec(txt='#\n# patches_base=1.2.3\n')
    spec.set_magic_comment('patches_ignore', 'DROP-IN-RPM')
    assert 'DROP-IN-RPM' == spec.get_magic_comment('patches_ignore')


def test_set_magic_comment_only_patches_ignore():
    spec = specfile.Spec(txt='\n# patches_ignore=foo\n\n')
    spec.set_magic_comment('patches_ignore', 'DROP-IN-RPM')
    assert 'DROP-IN-RPM' == spec.get_magic_comment('patches_ignore')


def test_create_new_magic_comment_foo():
    spec = specfile.Spec(txt='\nSource0: foo.tgz\n')
    spec._create_new_magic_comment('foo', 'bar')
    assert 'bar' == spec.get_magic_comment('foo')


def test_create_new_magic_comment_foo_existing_other_magic_comment():
    spec = specfile.Spec(txt='\nSource0: foo.tgz\n#\n#patches_base=1.2.3\n#\n')
    spec._create_new_magic_comment('foo', 'bar')
    assert 'bar' == spec.get_magic_comment('foo')


magic_comment_patches_base = '# patches_base=1.2.3'
magic_comment_foo = '# foo=bar'
source_leader = 'Source0: foo.tgz'
patches_leader = 'Patch0: foo.patch'


def test_create_new_mc_foo_existing_other_mc_with_ordering():
    mock_file = '\n'.join(['', source_leader, '#', magic_comment_patches_base,
                           '#', ''])
    spec = specfile.Spec(txt=mock_file)
    spec._create_new_magic_comment('foo', 'bar')

    lines = spec.txt.split('\n')
    assert magic_comment_foo in lines
    assert magic_comment_patches_base in lines
    # check ordering
    assert magic_comment_patches_base in lines[lines.index(magic_comment_foo):]


def test_create_new_mc_foo_existing_other_mc_and_patches_with_ordering():
    mock_file = '\n'.join(['', source_leader, '#', magic_comment_patches_base,
                           '#', patches_leader, ''])
    spec = specfile.Spec(txt=mock_file)
    spec._create_new_magic_comment('foo', 'bar')

    lines = spec.txt.split('\n')
    assert magic_comment_foo in lines
    assert patches_leader in lines
    # check ordering
    assert patches_leader in lines[lines.index(magic_comment_foo):]


def test_create_new_magic_comment_foo_source_and_patch():
    mock_file = '\n'.join(['', source_leader, patches_leader, ''])
    spec = specfile.Spec(txt=mock_file)
    spec._create_new_magic_comment('foo', 'bar')
    assert 'bar' == spec.get_magic_comment('foo')

    lines = spec.txt.split('\n')
    assert magic_comment_foo in lines
    # check ordering
    assert patches_leader in lines[lines.index(magic_comment_foo):]


def test_create_new_magic_comment_foo_existing_magic_comment_no_extra_lines():
    mock_file = '\n'.join(['', source_leader, '#', magic_comment_patches_base,
                           '#', ''])
    spec = specfile.Spec(txt=mock_file)
    spec._create_new_magic_comment('foo', 'bar')

    lines = spec.txt.split('\n')
    assert magic_comment_foo in lines
    assert magic_comment_patches_base in lines
    # check no-extra lines between
    index_mc_foo = lines.index(magic_comment_foo)
    index_mc_patches_base = lines.index(magic_comment_patches_base)
    assert len(lines[index_mc_foo + 1:index_mc_patches_base]) == 0


def test_create_new_mc_foo_existing_magic_comment_and_patch_no_extra_lines():
    mock_file = '\n'.join(['', source_leader, '#', magic_comment_patches_base,
                           '#', patches_leader, ''])
    spec = specfile.Spec(txt=mock_file)
    spec._create_new_magic_comment('foo', 'bar')

    lines = spec.txt.split('\n')
    assert magic_comment_foo in lines
    assert magic_comment_patches_base in lines
    # check no-extra lines between

    index_mc_foo = lines.index(magic_comment_foo)
    index_mc_patches_base = lines.index(magic_comment_patches_base)
    assert len(lines[index_mc_foo + 1:index_mc_patches_base]) == 0
    assert len(lines[index_mc_patches_base + 1:index_mc_foo]) == 0


def test_create_new_mc_comment_with_ge():
    mock_file = '\n'.join(['', source_leader, 'BuildRequires:    systemd',
                           '# Required to build nova.conf.sample',
                           'BuildRequires:    python%{pyver}-castellan '
                           '>= 0.16.0', ''])
    spec = specfile.Spec(txt=mock_file)
    spec._create_new_magic_comment('foo', 'bar')

    lines = spec.txt.split('\n')
    assert magic_comment_foo in lines
    # check ordering
    assert magic_comment_foo not in\
        lines[lines.index('BuildRequires:    systemd'):]


def test_get_requires_true(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'requires')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        got = spec.get_requires(True, True, True)
        expected = defaultdict(set)
        packages = [('python-argparse', '== 1.2.3'),
                    ('python-iso8601', '== 1.2.3'),
                    ('python-prettytable', '')]
        for name, version in packages:
            expected[name] = version
        assert got == expected


def test_get_requires_false(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'requires')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        got = spec.get_requires(False, False, False)
        expected = defaultdict(set)
        packages = [('python-argparse', '== 42:1.2.3'),
                    ('python-iso8601', '== 1.2.3'),
                    ('python3-prettytable', '')]
        for name, version in packages:
            if version:
                expected[name].add(version)
            else:
                expected[name]
        assert got == expected


def test_get_provides_true(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'requires')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        got = spec.get_provides(True, True, True)
        expected = defaultdict(set)
        packages = [('foo', '== 1.2.3-0.3')]
        for name, version in packages:
            expected[name] = version
        assert got == expected


def test_get_provides_false(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'requires')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        got = spec.get_provides(False, False, False)
        expected = defaultdict(set)
        packages = [('foo', '== 1:1.2.3-0.3')]
        for name, version in packages:
            if version:
                expected[name].add(version)
            else:
                expected[name]
        assert got == expected


def test_get_requires_not_provided_01(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'requires')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        got = spec.get_requires_not_provided(True, True, True)
        expected = defaultdict(set)
        packages = [('python-argparse', '== 1.2.3'),
                    ('python-iso8601', '== 1.2.3'),
                    ('python-prettytable', '')]
        for name, version in packages:
            expected[name] = version
        assert got == expected


def test_get_requires_not_provided_02(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'requires-not-provided')
    with dist_path.as_cwd():
        spec = specfile.Spec()
        got = spec.get_requires_not_provided(True, True, True)
        expected = defaultdict(set)
        packages = [('python-argparse', '== 1.2.3'),
                    ('python-iso8601', '== 1.2.3'),
                    ('python-prettytable', '')]
        for name, version in packages:
            expected[name] = version
        assert got == expected


def test_remove_python_requires_by_name(tmpdir):
    txt = '\n'.join(['Requires:     python-sqlalchemy',
                     'Requires:     python-prettytable >= 1.0.10',
                     'Requires:     python-iso8601'])
    spec = specfile.Spec(txt=txt)
    got = spec.remove_python_requires_by_name('python-sqlalchemy')
    assert got is True
    got = spec.remove_python_requires_by_name('python-prettytable')
    assert got is True
    assert 'Requires:     python-sqlalchemy' not in spec.txt
    assert 'Requires:     python-prettytable >= 1.0.10' not in spec.txt
    assert 'Requires:     python-iso8601' in spec.txt


def test_remove_python_requires_by_name_false(tmpdir):
    txt = '\n'.join(['Requires:     python-sqlalchemy >= 1.0.10',
                     'Requires:     python-prettytable',
                     'Requires:     python-iso8601'])
    spec = specfile.Spec(txt=txt)
    got = spec.remove_python_requires_by_name('python-argparse')
    assert got is False


def test_edit_python_requires_version_by_name_true(tmpdir):
    txt = '\n'.join(['Requires:     python-sqlalchemy >= 1.0.10',
                     '',
                     'BuildRequires:     python-sqlalchemy',
                     'Requires:     python-prettytable',
                     'Requires:     python3-iso8601 >= 1.0.0',
                     'Requires:     python-osc-lib >= 1.0.0'])
    spec = specfile.Spec(txt=txt)
    got = spec.edit_python_requires_version_by_name('python-sqlalchemy',
                                                    '>= 1.0.12')
    assert got is True
    assert 'Requires:     python-sqlalchemy >= 1.0.12\n\n' in spec.txt
    assert 'BuildRequires:     python-sqlalchemy\n' in spec.txt
    got = spec.edit_python_requires_version_by_name('python-prettytable',
                                                    '>= 1.0.1')
    assert got is True
    assert 'Requires:     python-prettytable >= 1.0.1\n' in spec.txt
    got = spec.edit_python_requires_version_by_name('python3-iso8601', '')
    assert got is True
    assert 'Requires:     python3-iso8601\n' in spec.txt


def test_edit_python_requires_version_by_name_false(tmpdir):
    txt = '\n'.join(['Requires:     python-sqlalchemy >= 1.0.10',
                     'Requires:     python-prettytable',
                     'Requires:     python-iso8601',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.edit_python_requires_version_by_name('python-argparse')
    assert got is False


def test_get_subpackages_1(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     '%package -n        python3-foo',
                     'Summary:           foo summary',
                     'Requires:          python-bar1',
                     '%description -n    python-foo',
                     '%{common_desc}',
                     '',
                     '%package           doc',
                     'Requires:          python-bar2',
                     '%description       doc',
                     '%{common_desc}',
                     '',
                     '%package test',
                     'Requires:          python-bar3',
                     '%description       test',
                     '%{common_desc}'])
    spec = specfile.Spec(txt=txt)
    subpkgs = spec.get_subpackages()
    assert subpkgs['python3-foo'] == (1, 4)
    assert subpkgs['openstack-foo-doc'] == (7, 9)
    assert subpkgs['openstack-foo-test'] == (12, 14)


def test_get_subpackages_2(tmpdir):
    txt = '\n'.join(['Name:            openstack-foo',
                     'Requires:        python3-foo1',
                     'BuildRequires:   python-baz1'])
    spec = specfile.Spec(txt=txt)
    assert spec.get_subpackages() is None


def test_find_last_dependency_1(tmpdir):
    txt = '\n'.join(['Requires:      python-foo1',
                     'Requires:      python-foo2',
                     'BuildRequires: python-bar1',
                     'PreReq:        is-deprecated',
                     'Requires:      python-foo3',
                     'Requires:      python-foo3'])
    spec = specfile.Spec(txt=txt)
    assert spec.find_last_dependency('Requires') == 5


def test_find_last_dependency_2(tmpdir):
    txt = '\n'.join(['BuildRequires: python-setuptools',
                     'PreReq:        is-deprecated'])
    spec = specfile.Spec(txt=txt)
    assert spec.find_last_dependency('Requires') is None


def test_find_last_dependency_3(tmpdir):
    txt = '\n'.join(['Requires:      python-foo1',
                     'Requires:      python-foo2',
                     'PreReq:        is-deprecated',
                     'Requires:      python-bar1',
                     'BuildRequires: python-baz1'])
    spec = specfile.Spec(txt=txt)
    assert spec.find_last_dependency('PreReq', 0, 2) == 2


def test_find_last_dependency_4(tmpdir):
    txt = '\n'.join(['Requires:      python-foo1',
                     'Requires:      python-foo2',
                     '%if 0%{?fedora}',
                     'Requires: qemu-kvm-core >= 2.8.0',
                     '%if 0%{?with_doc}',
                     'Requires:      python-foo3',
                     '%endif',
                     'Requires:      python-foo4',
                     '%endif'])
    spec = specfile.Spec(txt=txt)
    assert spec.find_last_dependency('Requires', 0, 8) == 1


def test_insert_dependency_after_1(tmpdir):
    txt = '\n'.join(['Requires:     python3-foo1',
                     'Requires:     python3-foo2',
                     'PreReq:       is-deprecated',
                     'Requires:     python3-bar1',
                     'BuildRequires:   python-baz1'])
    spec = specfile.Spec(txt=txt)
    assert spec.insert_dependency_after('python-bar2', 3) is True
    assert ("Requires:     python3-bar1\n"
            "Requires:     python3-bar2\n") in spec.txt


def test_insert_dependency_after_2(tmpdir):
    txt = '\n'.join(['BuildArch:    noarch',
                     ''])
    spec = specfile.Spec(txt=txt)
    assert spec.insert_dependency_after('python-bar2', 1) is True
    assert ("BuildArch:    noarch\n"
            "\n"
            "Requires: python3-bar2") in spec.txt


def test_insert_dependency_after_3(tmpdir):
    txt = '\n'.join(['BuildArch:    noarch'])
    spec = specfile.Spec(txt=txt)
    assert spec.insert_dependency_after('python-bar2', 1) is False


def test_add_python_requires_1_in_subpkg_after_last_found_requires(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     '%package -n        python3-foo',
                     'Summary:           foo summary',
                     'BuildRequires:     python3-bar1',
                     'Requires:          python3-bar2',
                     '%description -n    python3-foo',
                     '%{common_desc}',
                     '',
                     '%package -n        python3-foo-tests',
                     'Summary:           foo summary',
                     'BuildRequires:     python3-bar3',
                     'Requires:          python3-bar4',
                     '%description -n    python3-foo-tests',
                     '%{common_desc}'])
    spec = specfile.Spec(txt=txt)
    got = spec.add_python_requires('python-argparse', 'python3-foo')
    assert got is True
    assert ("Requires:          python3-bar2\n"
            "Requires:          python3-argparse\n"
            "%description -n    python3-foo") in spec.txt


def test_add_python_requires_2_in_main_package_with_subpkgs_present(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     '%package -n        python3-foo',
                     'BuildRequires:     python3-bar1',
                     'Requires:          python3-bar2',
                     '%description -n    python3-foo',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.add_python_requires('python-argparse')
    assert got is True
    assert ("BuildArch:         noarch\n"
            "Requires:         python3-argparse") in spec.txt


def test_add_python_requires_3_in_main_package_without_subpkgs_present(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     'BuildRequires:     python3-bar1',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.add_python_requires('python-argparse', '')
    assert got is True
    assert ("BuildRequires:     python3-bar1\n"
            "Requires:     python3-argparse") in spec.txt


def test_add_python_requires_4_raising_could_not_add_message(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'Summary:       This is foo summary.'])
    with pytest.raises(exception.CouldNotAddPythonRequires):
        spec = specfile.Spec(txt=txt)
        got = spec.add_python_requires('python-argparse', '')


def test_guess_main_python_subpackage_1(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     '%package -n        python3-foo',
                     'Requires:          python3-bar1',
                     '%description -n    python3-foo',
                     '%{common_desc}',
                     '%package -n        python3-foo-test',
                     'Requires:          python3-bar2',
                     '%description -n    python3-foo-test',
                     '%{common_desc}',
                     '%package -n        python3-foo-doc',
                     'Requires:          python3-bar3',
                     '%description -n    python3-foo-doc',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got == 'python3-foo'


def test_guess_main_python_subpackage_2_no_subpkgs_starting_w_python(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     '%package -n        openstack-foo',
                     'Requires:          python3-bar1',
                     '%description -n    openstack-foo',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got == "openstack-foo"


def test_guess_main_python_subpackage_3_no_subpackages(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got is None


def test_guess_main_python_subpackage_4_do_not_start_with_python(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     '%package           common',
                     'Requires:          python3-bar1',
                     '%description       common',
                     '%{common_desc}',
                     '%package -n        python3-foo-test',
                     'Requires: %{name}-common = %{version}-%{release}',
                     '%description -n    python3-foo-test',
                     '%{common_desc}',
                     '%package -n        python3-foo-doc',
                     'Requires: %{name}-common = %{version}-%{release}',
                     '%description -n    python3-foo-doc',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got == 'openstack-foo-common'


def test_guess_main_python_subpackage_5_at_the_end(tmpdir):
    txt = '\n'.join(['Name:              openstack-foo',
                     'BuildArch:         noarch',
                     '%package -n        openstack-foo-test',
                     'Requires: %{name}-common = %{version}-%{release}',
                     '%description -n    openstack-foo-test',
                     '%{common_desc}',
                     '%package -n        openstack-foo-doc',
                     'Requires: %{name}-common = %{version}-%{release}',
                     '%description -n    openstack-foo-doc',
                     '%{common_desc}',
                     '%package           common',
                     'Requires:          python3-bar1',
                     '%description       common',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got == 'openstack-foo-common'


def test_guess_main_python_subpackage_6(tmpdir):
    txt = '\n'.join(['Name:              python-foo',
                     'BuildArch:         noarch',
                     '%package -n        python3-foo',
                     'Requires: python-%{name}-lang = %{version}-%{release}',
                     '%description -n    python3-foo',
                     '%{common_desc}',
                     '%package -n        python-foo-lang',
                     'Summary: Translation files',
                     '%description -n    python-foo-lang',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got == 'python3-foo'


def test_guess_main_python_subpackage_7(tmpdir):
    txt = '\n'.join(['Name:              python-foo',
                     'BuildArch:         noarch',
                     '%package -n        python3-foo',
                     'Requires: python3-%{name}-test = %{version}-%{release}',
                     '%description -n    python3-foo',
                     '%{common_desc}',
                     '%package -n        python3-foo-test',
                     'Summary: Translation files',
                     '%description -n    python3-foo-test',
                     '%{common_desc}',
                     ''])
    spec = specfile.Spec(txt=txt)
    got = spec.guess_main_python_subpackage()
    assert got == 'python3-foo'
