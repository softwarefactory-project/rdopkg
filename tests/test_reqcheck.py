import pytest
import subprocess

from rdopkg.cli import rdopkg
from rdopkg.actionmods.reqs import CheckReq, DiffReq

import test_common as common


def _assert_sanity_out(o):
    assert 'None' not in o


def test_reqcheck(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'MISSING:' not in o


def test_checkreq_exclude_versions():
    cr = CheckReq('mypackage', '!= 1.2.6,!= 1.2.5,>= 1.2.3', '>= 1.2.3')
    got = cr.met()
    expected = True
    assert got == expected


def test_checkreq_max_capped_version():
    cr = CheckReq('mypackage', '<= 1.2.9,>= 1.2.3', '>= 1.2.3')
    got = cr.met()
    expected = True
    assert got == expected


def test_checkreq_version_not_capped_strictly_identical():
    cr = CheckReq('mypackage', '>= 1.2.3', '> 1.2.3')
    got = cr.met()
    expected = False
    assert got == expected


def test_checkreq_at_least_one_version_not_capped_01():
    cr = CheckReq('mypackage', '>= 1.2.3', '')
    got = cr.met()
    expected = False
    assert got == expected


def test_checkreq_at_least_one_version_not_capped_02():
    cr = CheckReq('mypackage', '', '>= 1.2.3')
    got = cr.met()
    expected = False
    assert got == expected


def test_checkreq_version_not_capped():
    cr = CheckReq('mypackage', '', '')
    got = cr.met()
    expected = True
    assert got == expected


def test_diffreq():
    dr = DiffReq('mypackage', '!=1.2.5,>=1.2.3')
    got = dr.__str__()
    expected = 'mypackage != 1.2.5,>= 1.2.3'
    assert got == expected


def test_diffreq_with_spaces():
    dr = DiffReq('mypackage', '   !=  1.2.5,  >=  1.2.3  ')
    got = dr.__str__()
    expected = 'mypackage != 1.2.5,>= 1.2.3'
    assert got == expected


def test_diffreq_new_version():
    dr = DiffReq('mypackage', '!=1.2.5,>=1.2.3')
    dr.vers = '!= 1.2.5,>= 1.2.4'
    got = dr.__str__()
    expected = 'mypackage != 1.2.5,>= 1.2.4  (was != 1.2.5,>= 1.2.3)'
    assert got == expected


def test_diffreq_old_version_not_capped():
    dr = DiffReq('mypackage', '')
    dr.vers = '>= 1.2.4'
    got = dr.__str__()
    expected = 'mypackage >= 1.2.4  (was not capped)'
    assert got == expected
