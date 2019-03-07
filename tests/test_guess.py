from rdopkg import guess
from collections import namedtuple
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock

VersionTestCase = namedtuple('VersionTestCase', ('expected', 'input_data'))


data_table_good = [
    VersionTestCase(('1.2.3', None), '1.2.3'),
    VersionTestCase(('1.2.3', 'vX.Y.Z'), 'v1.2.3'),
    VersionTestCase(('1.2.3', 'VX.Y.Z'), 'V1.2.3'),
    VersionTestCase(('banana', None), 'banana'),
]

data_table_bad = [
    VersionTestCase((None, None), None),
    VersionTestCase((None, None), []),
    VersionTestCase((None, None), ()),
    VersionTestCase((None, None), ''),
    VersionTestCase((None, None), {}),
]

data_table_ugly = [
    VersionTestCase((None, None), ('foo', 'bar', 'bah')),
    VersionTestCase((None, None), ['foo', 'bar', 'bah']),
    VersionTestCase((None, None), {'foo': 'bar'}),
]


def test_table_data_good_tag2version():
    for entry in data_table_good:
        assert entry.expected == guess.tag2version(entry.input_data)


def test_table_data_bad_tag2version():
    for entry in data_table_bad:
        # Input Validation should probably return to us (None, None)
        # assert entry.expected == guess.tag2version(entry.input_data)
        assert (entry.input_data, None) == guess.tag2version(entry.input_data)


def test_table_data_ugly_tag2version():
    for entry in data_table_ugly:
        # TODO: probably should be a more specific exception
        with pytest.raises(Exception):
            guess.tag2version(entry.input_data)


def test_version2tag_simple():
    assert '1.2.3' == guess.version2tag('1.2.3')


def test_version2tag_type1():
    assert 'v1.2.3' == guess.version2tag('1.2.3', 'vX.Y.Z')


def test_version2tag_type2():
    assert 'V1.2.3' == guess.version2tag('1.2.3', 'VX.Y.Z')


find_patches_data = [
        ('rhos-15.0-rhel-8', ['rhos-15.0-patches'], 'rhos-15.0-patches'),
        ('foo-bar', ['foo-patches'], 'foo-patches'),
        ('foo-bar', ['foo-bar-patches'], 'foo-bar-patches'),
        ('foo-bar', ['refs/remotes/patches/foo-bar-patches'], 'foo-bar-patches'),
        ('foo-bar', [''], None),

        ('rhos-15.0-rhel-8-trunk', ['rhos-15.0-trunk-patches'], 'rhos-15.0-trunk-patches'),
    ]


@patch('rdopkg.guess.git')
def test_find_patches_branch(git_mock):
    git_mock.config_get = MagicMock(return_value='')
    def ref_exists(path):
        data = ['rhos-15.0-patches', 'refs/remotes/patches/rhos-15.0-patches']
        return path in data
    git_mock.ref_exists = ref_exists

    # TODO Mock git.config_get('rdopkg.<distgit>.patches-branch')
    # TODO Mock git.ref_exists(<path>) to check paths in list
    expected = 'patches/rhos-15.0-patches'
    remote = 'patches'
    distgit = 'rhos-15.0-rhel-8'
    assert expected == guess.find_patches_branch(distgit, remote)

@patch('rdopkg.guess.git')
def test_find_patches_branch_2(git_mock):
    git_mock.config_get = MagicMock(return_value='')
    def ref_exists(path):
        data = [
                'rhos-15.0-trunk-patches',
                'refs/remotes/patches/rhos-15.0-trunk-patches',
                'rhos-15.0-rhel-8-trunk-patches',
                'refs/remotes/patches/rhos-15.0-rhel-8-trunk-patches'
                'rhos-15.0-patches',
                'refs/remotes/patches/rhos-15.0-patches'
            ]
        return path in data
    git_mock.ref_exists = ref_exists

    # TODO Mock git.config_get('rdopkg.<distgit>.patches-branch')
    # TODO Mock git.ref_exists(<path>) to check paths in list
    expected = 'patches/rhos-15.0-trunk-patches'
    remote = 'patches'
    distgit = 'rhos-15.0-rhel-8-trunk'
    assert expected == guess.find_patches_branch(distgit, remote)
