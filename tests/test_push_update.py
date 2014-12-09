import os
import shutil

import rdopkg.shell
from rdopkg.utils.cmd import git

from common import ASSETS_DIR
from common import cfind


FILE_LISTS = {
    'griz.yml': {
        'grizzly/epel-6/potato-1.0.0-3.el6.noarch.rpm',
        'grizzly/epel-6/potato-1.0.0-3.el6.src.rpm',
        'grizzly/fedora-20/potato-1.0.0-2.fc21.noarch.rpm',
        'grizzly/fedora-20/potato-1.0.0-2.fc21.src.rpm',
    },
    'iceh.yml': {
        'icehouse/epel-6/banana-1.0.0-3.el6.noarch.rpm',
        'icehouse/epel-6/banana-1.0.0-3.el6.src.rpm',
        'icehouse/fedora-20/banana-1.0.0-2.fc21.noarch.rpm',
        'icehouse/fedora-20/banana-1.0.0-2.fc21.src.rpm',
    },
    'hava.yml': {
        'havana/epel-6/orange-1.0.0-3.el6.noarch.rpm',
        'havana/epel-6/orange-1.0.0-3.el6.src.rpm',
        'havana/fedora-20/orange-1.0.0-2.fc21.noarch.rpm',
        'havana/fedora-20/orange-1.0.0-2.fc21.src.rpm',
    },
}


def setup_module(module):
    bin_path = os.path.abspath(os.path.join(ASSETS_DIR, 'bin'))
    os.environ['PATH'] = '%s:%s' % (bin_path, os.environ['PATH'])


def prep_push_test(tmpdir, update_repo, dest):
    rdoup_path = tmpdir.join('rdo-update')
    dest_path = tmpdir.join('dest')
    shutil.copytree(os.path.join(ASSETS_DIR, 'rdo-update.git', update_repo),
                    str(rdoup_path))
    shutil.copytree(os.path.join(ASSETS_DIR, 'dest', dest), str(dest_path))
    with rdoup_path.as_cwd():
        git('init')
        git('add', '.')
        git('commit', '-m', 'Initial import')
    return rdoup_path, dest_path


def assert_files_list(file_list_path, dest_base, files):
    lines = file(file_list_path, 'r').readlines()
    pkgs = set()
    for line in lines:
        line = line.rstrip()
        assert line.startswith(dest_base)
        pkg = line[len(dest_base):]
        pkgs.add(pkg)
    assert set(files) == pkgs


def test_push_one_clean(tmpdir):
    rdoup_path, dest_path = prep_push_test(tmpdir, 'one_added', 'clean')
    dest_base = str(dest_path.join('openstack-'))
    with tmpdir.as_cwd():
        rdopkg.shell.main(cargs=['push-updates', str(rdoup_path), dest_base])

    # pushed packages
    tree = cfind(dest_path)
    exp_tree = {
        './openstack-grizzly',
        './openstack-grizzly/EMPTY',
        './openstack-havana',
        './openstack-havana/EMPTY',
        './openstack-icehouse',
        './openstack-icehouse/EMPTY',
        './openstack-icehouse/epel-6',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.noarch.rpm',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.src.rpm',
        './openstack-icehouse/fedora-20',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.noarch.rpm',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.src.rpm',
        './sign-rpms',
    }
    assert tree == exp_tree

    # rdo-update repo changes
    tree = cfind(rdoup_path, include_dirs=False)
    exp_tree = {
        './pushed/iceh.yml',
        './pushed/iceh.yml.files',
    }
    assert tree == exp_tree

    # list of pushed files
    assert_files_list(
        str(rdoup_path.join('pushed/iceh.yml.files')), dest_base,
        FILE_LISTS['iceh.yml'])


def test_push_one_collision(tmpdir):
    rdoup_path, dest_path = prep_push_test(tmpdir, 'one_added', 'collision')
    dest_base = str(dest_path.join('openstack-'))
    pre_rdoup_tree = cfind(rdoup_path)
    pre_dest_tree = cfind(dest_path)
    with tmpdir.as_cwd():
        rdopkg.shell.main(cargs=['push-updates', str(rdoup_path), dest_base])
    # Nothing should change on collision - ensure rollback
    dest_tree = cfind(dest_path)
    assert dest_tree == pre_dest_tree
    rdoup_tree = cfind(rdoup_path)
    assert rdoup_tree == pre_rdoup_tree


def test_push_all_mixed_clean(tmpdir):
    rdoup_path, dest_path = prep_push_test(tmpdir, 'mixed', 'clean')
    dest_base = str(dest_path.join('openstack-'))
    with tmpdir.as_cwd():
        rdopkg.shell.main(cargs=['push-updates', str(rdoup_path), dest_base])

    tree = cfind(dest_path)
    exp_tree = {
        './openstack-grizzly',
        './openstack-grizzly/EMPTY',
        './openstack-havana',
        './openstack-havana/EMPTY',
        './openstack-havana/epel-6',
        './openstack-havana/epel-6/orange-1.0.0-3.el6.noarch.rpm',
        './openstack-havana/epel-6/orange-1.0.0-3.el6.src.rpm',
        './openstack-havana/fedora-20',
        './openstack-havana/fedora-20/orange-1.0.0-2.fc21.noarch.rpm',
        './openstack-havana/fedora-20/orange-1.0.0-2.fc21.src.rpm',
        './openstack-icehouse',
        './openstack-icehouse/EMPTY',
        './openstack-icehouse/epel-6',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.noarch.rpm',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.src.rpm',
        './openstack-icehouse/fedora-20',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.noarch.rpm',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.src.rpm',
        './sign-rpms',
    }
    assert tree == exp_tree

    tree = cfind(rdoup_path, include_dirs=False)
    # failed update shoud remain as well as updates outside of ready/
    assert tree == {
        './pushed/hava.yml',
        './pushed/hava.yml.files',
        './pushed/iceh.yml',
        './pushed/iceh.yml.files',
        './ready/fail.yml',
        './updates/griz.yml',
    }

    assert_files_list(
        str(rdoup_path.join('pushed/iceh.yml.files')), dest_base,
        FILE_LISTS['iceh.yml'])
    assert_files_list(
        str(rdoup_path.join('pushed/hava.yml.files')), dest_base,
        FILE_LISTS['hava.yml'])


def test_push_all_mixed_collision(tmpdir):
    rdoup_path, dest_path = prep_push_test(tmpdir, 'mixed', 'collision')
    dest_base = str(dest_path.join('openstack-'))
    with tmpdir.as_cwd():
        rdopkg.shell.main(cargs=['push-updates', str(rdoup_path), dest_base])

    tree = cfind(dest_path)
    exp_tree = {
        './openstack-grizzly',
        './openstack-grizzly/EMPTY',
        './openstack-havana',
        './openstack-havana/epel-6',
        './openstack-havana/epel-6/banana-1.0.0-3.el6.src.rpm',
        './openstack-havana/epel-6/orange-1.0.0-3.el6.noarch.rpm',
        './openstack-havana/epel-6/orange-1.0.0-3.el6.src.rpm',
        './openstack-havana/fedora-20',
        './openstack-havana/fedora-20/orange-1.0.0-2.fc21.noarch.rpm',
        './openstack-havana/fedora-20/orange-1.0.0-2.fc21.src.rpm',
        './openstack-icehouse',
        './openstack-icehouse/epel-6',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.src.rpm',
        './sign-rpms',
        }
    assert tree == exp_tree

    tree = cfind(rdoup_path, include_dirs=False)
    # failed update shoud remain as well as updates outside of ready/
    assert tree == {
        './pushed/hava.yml',
        './pushed/hava.yml.files',
        './ready/fail.yml',
        './ready/iceh.yml',
        './updates/griz.yml',
        }

    assert_files_list(
        str(rdoup_path.join('pushed/hava.yml.files')), dest_base,
        FILE_LISTS['hava.yml'])

def test_push_all_mixed_collision_overwrite(tmpdir):
    rdoup_path, dest_path = prep_push_test(tmpdir, 'mixed', 'collision')
    dest_base = str(dest_path.join('openstack-'))
    with tmpdir.as_cwd():
        rdopkg.shell.main(
            cargs=['push-updates', str(rdoup_path), dest_base, '-w'])

    tree = cfind(dest_path)
    exp_tree = {
        './openstack-grizzly',
        './openstack-grizzly/EMPTY',
        './openstack-havana',
        './openstack-havana/epel-6',
        './openstack-havana/epel-6/banana-1.0.0-3.el6.src.rpm',
        './openstack-havana/epel-6/orange-1.0.0-3.el6.noarch.rpm',
        './openstack-havana/epel-6/orange-1.0.0-3.el6.src.rpm',
        './openstack-havana/fedora-20',
        './openstack-havana/fedora-20/orange-1.0.0-2.fc21.noarch.rpm',
        './openstack-havana/fedora-20/orange-1.0.0-2.fc21.src.rpm',
        './openstack-icehouse',
        './openstack-icehouse/epel-6',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.src.rpm',
        './openstack-icehouse/fedora-20',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.noarch.rpm',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.src.rpm',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.noarch.rpm',
        './sign-rpms',
    }
    assert tree == exp_tree

    tree = cfind(rdoup_path, include_dirs=False)
    # failed update shoud remain as well as updates outside of ready/
    assert tree == {
        './pushed/hava.yml',
        './pushed/hava.yml.files',
        './pushed/iceh.yml',
        './pushed/iceh.yml.files',
        './ready/fail.yml',
        './updates/griz.yml',
    }

    assert_files_list(
        str(rdoup_path.join('pushed/hava.yml.files')), dest_base,
        FILE_LISTS['hava.yml'])


def test_push_selected_mixed_clean(tmpdir):
    rdoup_path, dest_path = prep_push_test(tmpdir, 'mixed', 'clean')
    dest_base = str(dest_path.join('openstack-'))
    with tmpdir.as_cwd():
        rdopkg.shell.main(cargs=['push-updates',
                                 str(rdoup_path), dest_base,
                                 '-f', 'ready/iceh.yml', 'updates/griz.yml',
                                 ])

    tree = cfind(dest_path)
    exp_tree = {
        './openstack-grizzly',
        './openstack-grizzly/EMPTY',
        './openstack-grizzly/epel-6',
        './openstack-grizzly/epel-6/potato-1.0.0-3.el6.noarch.rpm',
        './openstack-grizzly/epel-6/potato-1.0.0-3.el6.src.rpm',
        './openstack-grizzly/fedora-20',
        './openstack-grizzly/fedora-20/potato-1.0.0-2.fc21.noarch.rpm',
        './openstack-grizzly/fedora-20/potato-1.0.0-2.fc21.src.rpm',
        './openstack-havana',
        './openstack-havana/EMPTY',
        './openstack-icehouse',
        './openstack-icehouse/EMPTY',
        './openstack-icehouse/epel-6',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.noarch.rpm',
        './openstack-icehouse/epel-6/banana-1.0.0-3.el6.src.rpm',
        './openstack-icehouse/fedora-20',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.noarch.rpm',
        './openstack-icehouse/fedora-20/banana-1.0.0-2.fc21.src.rpm',
        './sign-rpms',
    }
    assert tree == exp_tree

    tree = cfind(rdoup_path, include_dirs=False)
    assert tree == {
        './ready/fail.yml',
        './ready/hava.yml',
        './pushed/iceh.yml',
        './pushed/iceh.yml.files',
        './pushed/griz.yml',
        './pushed/griz.yml.files',
    }

    assert_files_list(
        str(rdoup_path.join('pushed/iceh.yml.files')), dest_base,
        FILE_LISTS['iceh.yml'])
    assert_files_list(
        str(rdoup_path.join('pushed/griz.yml.files')), dest_base,
        FILE_LISTS['griz.yml'])
