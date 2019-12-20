import pytest
import subprocess

from rdopkg.cli import rdopkg
from rdopkg.actionmods.reqs import *
from rdopkg.exception import WrongPythonVersion

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


def test_reqcheck_excess(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-excess')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'ADDITIONAL REQUIRES:' in o

def test_reqcheck_wrong_python_version(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck')
    with dist_path.as_cwd():
        with pytest.raises(WrongPythonVersion):
            rv = rdopkg('reqcheck', '-R', 'master', '-p', 'wrong')


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


def test_parse_reqs_txt_exact_output(caplog):
    requirements_txt = '\n'.join(['# The order of packages is significant',
                                  'argparse!=0.8.9,>=0.8.4 # MIT',
                                  'oslo.utils>=3.33.0',
                                  '',
                                  'WebOb>1.7.1 # MIT'])
    got = parse_reqs_txt(requirements_txt)
    for record in caplog.records:
        assert record.levelname != "WARNING"
    assert len(got) == 3


def test_parse_reqs_txt_with_spaces():
    requirements_txt = '  argparse    >=    0.8   '
    prt = parse_reqs_txt(requirements_txt)
    got = prt[0]
    assert got.name == 'argparse'
    assert got.vers == '>= 0.8'


def test_parse_reqs_txt_fail_to_parse_req_01(caplog):
    requirements_txt = '\n'.join(['argparse>=0.8.10 # MIT',
                                  'monotonic:0.6'])
    got = parse_reqs_txt(requirements_txt)
    for record in caplog.records:
        assert record.levelname == "WARNING"
    assert 'Failed to parse requirement' in caplog.text
    assert len(got) == 1


def test_parse_reqs_txt_fail_to_parse_req_02(caplog):
    requirements_txt = '\n'.join(['$=#wrong',
                                  'monotonic==0.6',
                                  'argparse>=0.8.10'])
    got = parse_reqs_txt(requirements_txt)
    for record in caplog.records:
        assert record.levelname == "WARNING"
    assert 'Failed to parse requirement' in caplog.text
    assert len(got) == 2


def test_parse_reqs_txt_empty(caplog):
    requirements_txt = ''
    got = parse_reqs_txt(requirements_txt)
    for record in caplog.records:
        assert record.levelname == "WARNING"
    assert 'The requirements.txt file is empty' in caplog.text
    assert len(got) == 0


def test_parse_reqs_txt_with_environment_marker_01(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version=='3.5'\
                                  or python_version=='3.6'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_parse_reqs_txt_with_environment_marker_02(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version=='3.3'\
                                  or python_version=='3.4'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 0


def test_parse_reqs_txt_with_environment_marker_03(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version>='3.4'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_parse_reqs_txt_with_environment_marker_04(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version>'3.6'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 0


def test_parse_reqs_txt_with_environment_marker_05(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version<'3.7'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_parse_reqs_txt_with_environment_marker_06(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version<'3.4'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 0


def test_parse_reqs_txt_with_environment_marker_07(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version<='3.6'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_parse_reqs_txt_with_environment_marker_08(caplog):
    requirements_txt = '\n'.join(["ipaddress==1.0.17;python_version>='3.6'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_parse_reqs_txt_with_environment_marker_09(caplog):
    requirements_txt = '\n'.join(["enum34==1.0.4;python_version=='2.7'\
                                   or python_version=='2.6'\
                                   or python_version=='3.6'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_parse_reqs_txt_with_environment_marker_10(caplog):
    requirements_txt = '\n'.join(["enum34==1.0.4;python_version=='2.7'\
                                   or python_version=='2.6'\
                                   or python_version=='3.3'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 0


def test_parse_reqs_txt_with_environment_marker_11(caplog):
    requirements_txt = '\n'.join(["enum34==1.0.4;platform_system=='Linux'"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1
