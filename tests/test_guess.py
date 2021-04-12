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
    with pytest.raises(TypeError):
        guess.tag2version(input_data)


def test_version2tag_simple():
    assert guess.version2tag('1.2.3') == '1.2.3'


def test_version2tag_type1():
    assert guess.version2tag('1.2.3', 'vX.Y.Z') == 'v1.2.3'


def test_version2tag_type2():
    assert guess.version2tag('1.2.3', 'VX.Y.Z') == 'V1.2.3'


def test_osdist_current_branch(monkeypatch):
    monkeypatch.setattr(guess, 'current_branch', lambda **kw: 'master')
    assert guess.osdist() == 'RDO'


@pytest.mark.parametrize('branch,expected', [
    ('master', 'RDO'),
    ('f33', 'RDO'),
    ('epel7', 'RDO'),
    ('epel8', 'RDO'),
    ('rh-1-rhel-8', 'RHOS'),
    ('rhos-17.0-rhel-8', 'RHOS'),
    ('ceph-4.0-rhel-7', 'RHCEPH'),
    ('ceph-5.0-rhel-8', 'RHCEPH'),
    ('rhscon-2-rhel-7', 'RHSCON'),
    ('eng-rhel-6', 'RHENG'),
    ('eng-rhel-7', 'RHENG'),
    ('eng-rhel-8', 'RHENG'),
    ('unknown', 'RDO'),
    ('private-kdreyer-ceph-5.0-rhel-8', 'RHCEPH'),
    ('hotfix-ceph-5.0-rhel-8-bz1234', 'RHCEPH'),
])
def test_osdist_branches(branch, expected):
    assert guess.osdist(branch=branch) == expected
