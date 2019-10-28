import pytest
import subprocess

from rdopkg.cli import rdopkg
from rdopkg.actionmods.reqs import CheckReq

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


def test_checkreq_01():
    cr = CheckReq('mypackage', '>= 1.2.3,!= 1.2.5', '>= 1.2.3')
    got = cr.met()
    expected = True
    assert got == expected


def test_checkreq_02():
    cr = CheckReq('mypackage', '>= 1.2.3', '> 1.2.3')
    got = cr.met()
    expected = False
    assert got == expected


def test_checkreq_03():
    cr = CheckReq('mypackage', '>= 1.2.3', '')
    got = cr.met()
    expected = False
    assert got == expected


def test_checkreq_04():
    cr = CheckReq('mypackage', '', '>= 1.2.3')
    got = cr.met()
    expected = False
    assert got == expected


def test_checkreq_05():
    cr = CheckReq('mypackage', '', '')
    got = cr.met()
    expected = True
    assert got == expected
