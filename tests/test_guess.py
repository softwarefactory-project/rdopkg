from rdopkg import guess
from collections import namedtuple
import pytest

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
