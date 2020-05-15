from rdopkg import guess
import pytest


@pytest.mark.parametrize('input_data,expected', [
    ('1.2.3', ('1.2.3', None)),
    ('v1.2.3', ('1.2.3', 'vX.Y.Z')),
    ('V1.2.3', ('1.2.3', 'VX.Y.Z')),
    ('banana', ('banana', None)),
])
def test_good_tag2version(input_data, expected):
    assert guess.tag2version(input_data) == expected


@pytest.mark.parametrize('input_data', [
    None,
    [],
    (),
    '',
    {},
])
def test_bad_tag2version(input_data):
    # Input Validation should probably return to us (None, None)
    assert guess.tag2version(input_data) == (input_data, None)


@pytest.mark.parametrize('input_data', [
    ('foo', 'bar', 'bah'),
    ['foo', 'bar', 'bah'],
    {'foo': 'bar'},
])
def test_ugly_tag2version(input_data):
    # TODO: probably should be a more specific exception
    with pytest.raises(Exception):
        guess.tag2version(input_data)


def test_version2tag_simple():
    assert guess.version2tag('1.2.3') == '1.2.3'


def test_version2tag_type1():
    assert guess.version2tag('1.2.3', 'vX.Y.Z') == 'v1.2.3'


def test_version2tag_type2():
    assert guess.version2tag('1.2.3', 'VX.Y.Z') == 'V1.2.3'
