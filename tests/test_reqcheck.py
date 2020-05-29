import pytest
import subprocess
import time

from rdopkg.cli import rdopkg
from rdopkg.actionmods.reqs import *
from rdopkg.actions.reqs.actions import *
from rdopkg.exception import WrongPythonVersion

import test_common as common


def _assert_sanity_out(o):
    assert 'None' not in o


def test_reqcheck(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-S', '-R', 'master')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'EXCESS:' not in o
    assert 'MISMATCH:' not in o
    assert 'MISSING:' not in o
    assert 'REMOVED:' not in o
    assert rv == 0


def test_reqcheck_missing(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-missing')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-S', '-R', 'master')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'MISSING:' in o
    assert rv == 2


def test_reqcheck_mismatch(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-mismatch')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-S', '-R', 'master')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'MISMATCH:' in o
    assert rv == 4


def test_reqcheck_excess(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-excess')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-S', '-R', 'master')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'EXCESS:' in o
    assert rv == 0


def test_reqcheck_overridden_1(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-1.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'has been overridden' in o


def test_reqcheck_overridden_2(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-3.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'has been overridden' in o
    assert 'python-sqlalchemy >= 1.1.0' in o


def test_reqcheck_overridden_3(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-6.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'has been overridden' in o
    assert 'python-sqlalchemy >= 1.2.0' in o


def test_reqcheck_overridden_ignore_missing_true(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-7.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'python-tooz' not in o


def test_reqcheck_overridden_ignore_missing_false(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-8.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'python-tooz' in o


def test_reqcheck_overridden_nothing(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-4.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'has been overridden' not in o


def test_reqcheck_overridden_ignore(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        rv = rdopkg('reqcheck', '-R', 'master', '-O', 'overrides-file-2.yml')
    cap = capsys.readouterr()
    o = cap.out
    _assert_sanity_out(o)
    assert 'python-prettytable' not in o
    assert 'python-argparse' not in o
    assert 'python-iso8601' not in o


def test_reqcheck_overridden_error_parsing_file(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-overridden')
    with dist_path.as_cwd():
        with pytest.raises(SystemExit):
            rv = rdopkg('reqcheck', '-R', 'master', '-O',
                        'overrides-file-5.yml')


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


def test_checkreq_extract():
    cr = CheckReq('mypackage', '!= 1.2.5,>= 1.2.3', '')
    assert cr.desired_vers == '>= 1.2.3'


def test_checkreq_extract_no_match():
    cr = CheckReq('mypackage', '!= 1.2.5,!= 1.2.3', '')
    assert cr.desired_vers == '!= 1.2.5,!= 1.2.3'


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


def test_get_reqs_from_ref_not_requirements_file(tmpdir):
    # this spec dir does not contain requirements.txt
    dist_path = common.prep_spec_test(tmpdir, 'some')
    with dist_path.as_cwd():
        txt = get_reqs_from_ref('master', '3.6')
    assert txt == []


def test_get_pkgs_from_upstream_refs_1(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck')
    dist_path_remote = common.prep_spec_test(tmpdir, 'reqcheck-excess')
    with dist_path_remote.as_cwd():
        git('checkout', '-b', 'stable/rel-1')
        common.do_patch('foofile', '# a change', 'Dummy patch')

        git('checkout', 'master')
        time.sleep(1)

        git('checkout', '-b', 'stable/rel-2')
        common.add_line('requirements.txt', 'pbr>=2.0.0')
        git('add', '-f', 'requirements.txt')
        git('commit', '-m', 'Add pbr')

    with dist_path.as_cwd():
        git('remote', 'add', 'upstream', dist_path_remote.__str__())
        git('fetch', 'upstream')
        rel2_branched = git.get_commits_of_branch('upstream/stable/rel-2')
        got = get_pkgs_present_in_upstream_before(
            rel2_branched[0]['timestamp'])

    expected = ['python-argparse',
                'python-iso8601',
                'python-prettytable',
                'python-sqlalchemy']
    assert got == expected
    assert 'python-pbr' not in got


def test_get_pkgs_from_upstream_refs_2(tmpdir):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck')
    dist_path_remote = common.prep_spec_test(tmpdir, 'reqcheck-excess')
    with dist_path_remote.as_cwd():
        git('checkout', '-b', 'stable/rel-1')
        common.do_patch('foofile', '# a change', 'Dummy patch')

        git('checkout', 'master')

        git('checkout', '-b', 'stable/rel-2')
        common.add_line('requirements.txt', 'pbr>=2.0.0')
        git('add', '-f', 'requirements.txt')
        git('commit', '-m', 'Add pbr')

    with dist_path.as_cwd():
        git('remote', 'add', 'upstream', dist_path_remote.__str__())
        git('fetch', 'upstream')
        rel2_branched = git.get_commits_of_branch('upstream/stable/rel-2')
        got = get_pkgs_present_in_upstream_before(
            rel2_branched[0]['timestamp'] + str(1))

    expected = ['python-argparse',
                'python-iso8601',
                'python-prettytable',
                'python-sqlalchemy',
                'python-pbr']
    assert got == expected
    assert 'python-pbr' in got


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


def test_parse_reqs_txt_with_prerelease_version(caplog):
    requirements_txt = '\n'.join(["enum34==1.0.4.0rc1"])
    got = parse_reqs_txt(requirements_txt, '3.6')
    assert len(got) == 1


def test_reqcheck_autosync(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-autosync')
    check = ([],
             [],
             [CheckReq('python-to-be-edited-3', '>= 1.0.0', ''),
              CheckReq('python-to-be-edited4', '', '2.0.1'),
              CheckReq('python-to-be-edited5', '>= 1.0.12', '>= 1.0.10')],
             [CheckReq('python-to-be-added6', '>= 1.0.0', ''),
              CheckReq('python-to-be-added-7', '>= 4.27.0', ''),
              CheckReq('python-to-be-added8', '', '')],
             [],
             [CheckReq('python-to-be-removed1', '', ''),
              CheckReq('python-to-be-removed-2', '', '')])
    with dist_path.as_cwd():
        ra = reqcheck_autosync(check, True)
        spec_file = open('foo.spec', 'r')
        rp = reqcheck_print(check, 'text')
        _file = spec_file.readlines()
        spec_file.close()
    cap = capsys.readouterr()
    o = cap.out
    assert 'Requires:         python3-to-be-removed1\n' not in _file
    assert "- python-to-be-removed1" in o
    assert 'Requires:         python3-to-be-removed-2\n' not in _file
    assert "- python-to-be-removed-2" in o
    assert 'Requires:         python3-to-be-edited-3 >= 1.0.0\n' in _file
    assert "~ python-to-be-edited-3" in o
    assert 'Requires:         python3-to-be-edited4\n' in _file
    assert "~ python-to-be-edited4" in o
    assert 'Requires:         python3-to-be-edited5 >= 1.0.12\n' in _file
    assert "~ python-to-be-edited5 >= 1.0.12" in o
    assert 'Requires:         python3-to-be-added6 >= 1.0.0\n' in _file
    assert "+ python-to-be-added6 >= 1.0.0" in o
    assert 'Requires:         python3-to-be-added-7 >= 4.27.0\n' in _file
    assert "+ python-to-be-added-7 >= 4.27.0" in o


def test_reqcheck_autosync_error(tmpdir, capsys):
    dist_path = common.prep_spec_test(tmpdir, 'reqcheck-autosync')
    check = ([],
             [],
             [CheckReq('python-to-be-edited9', '>= 1.0.0', '')],
             [CheckReq('python-to-be-added10', '>= 1.0.0', '')],
             [],
             [CheckReq('python-to-be-removed11', '', '')])
    with dist_path.as_cwd():
        ra = reqcheck_autosync(check, True)
        rp = reqcheck_print(check, 'text')
        spec_file = open('foo.spec', 'r')
        _file = spec_file.readlines()
        spec_file.close()
    cap = capsys.readouterr()
    o = cap.out
    assert check[2][0].autosync_error_msg == "Unabled to edit the module"
    assert "Unabled to edit the module" in o
    assert 'Requires:         python3-to-be-edited9 #fail\n' in _file
    assert check[5][0].autosync_error_msg == "Unabled to remove the module"
    assert "Unabled to remove the module" in o
    assert 'Requires:         python3-to-be-removed11 #fail\n' in _file

    check = ([], [], [],
             [CheckReq('python-to-be-added10', '>= 1.0.0', '')], [], [])
    dist_path_2 = common.prep_spec_test(
        tmpdir,
        'reqcheck-autosync-fails-adding-requires')
    with dist_path_2.as_cwd():
        ra = reqcheck_autosync(check, True)
        rp = reqcheck_print(check, 'text')
        spec_file = open('foo.spec', 'r')
        _file = spec_file.readlines()
        spec_file.close()
    cap = capsys.readouterr()
    o = cap.out
    assert check[3][0].autosync_error_msg == ("Unabled to add the python "
                                              "Requires (no Requires, BR or "
                                              "BuildArch found in the spec "
                                              "file)")
    assert "Unabled to add the python Requires" in o
    assert 'Requires:         python3-to-be-added10\n' not in _file
