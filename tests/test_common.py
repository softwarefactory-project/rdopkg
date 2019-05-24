from __future__ import unicode_literals

import os
import py
import re
import shutil

from rdopkg.utils.cmd import encode
from rdopkg.utils.git import git
from rdopkg.utils.specfile import Spec
from rdopkg import exception


ASSETS_DIR = 'tests/assets'
DIST_POSTFIX = '%{?dist}'


def ffind(path='.', include_dirs=True):
    tree = set()
    for root, dirs, files in os.walk(path):
        if include_dirs:
            for f in dirs:
                tree.add(os.path.join(root, f))
        for f in files:
            tree.add(os.path.join(root, f))
    return tree


def cfind(path, include_dirs=True):
    if not hasattr(path, 'as_cwd'):
        path = py.path.local(path=path)
    with path.as_cwd():
        t = ffind(include_dirs=include_dirs)
    t = set(filter(lambda x: not x.startswith('./.'), t))
    return t


def distgit_path(dg):
    return os.path.join(ASSETS_DIR, 'spec', dg)


def spec_path(dg):
    return os.path.join(distgit_path(dg), 'foo.spec')


def prep_spec_test(tmpdir, distgit):
    dist_path = tmpdir.join('dist')
    shutil.copytree(os.path.join(ASSETS_DIR, 'spec', distgit),
                    str(dist_path))
    with dist_path.as_cwd():
        git('init')
        git('add', '.')
        git('commit', '-m', 'Initial import',
            isolated=True)
    return dist_path


def prep_patches_branch(tag='1.2.3'):
    git('checkout', '--orphan', 'master-patches')
    f = open('foofile', 'w')
    f.write("#not really a patch\n")
    f.close()
    git('add', 'foofile')
    git('commit', '-m', 'Create this test branch',
        isolated=True)
    if tag:
        git('tag', tag)
    git('checkout', 'master')


def do_patch(fn, content, msg):
    f = open(fn, 'w')
    content = encode(content)
    f.write(content)
    f.close()
    git('add', fn)
    git('commit', '-m', msg,
        isolated=True)


def add_patches(extra=False, filtered=False, tag=None):
    git('checkout', 'master-patches')
    if extra:
        do_patch('foofile', "#meh\n", 'Look, excluded patch')
        do_patch('foofile', "#nope\n", 'Yet another excluded patch')
    do_patch('foofile', "#huehue, change\n", 'Crazy first patch')
    if filtered:
        do_patch('foofile', "#fix ci\n", 'DROP-IN-RPM: ci fix')
        do_patch('foofile', "#and now for real\n", 'DROP-IN-RPM: moar ci fix')
    do_patch('foofile', "#lol, another change\n", 'Epic bugfix of doom MK2')
    if filtered:
        do_patch('foofile', "#oooops\n", 'DROP-IN-RPM: even moar ci fix')
    if tag:
        git('tag', tag)
    git('checkout', 'master')


def add_n_patches(n):
    git('checkout', 'master-patches')
    for i in range(1, n + 1):
        do_patch('foofile', "#extra patch %d\n" % i, 'Extra patch %d' % i)
    git('checkout', 'master')


def remove_patches(n):
    git('checkout', 'master-patches')
    git('reset', '--hard', 'HEAD' + n * '~')
    git('checkout', 'master')


def assert_distgit(dg_path, img_dg):
    img_path = distgit_path(img_dg)
    current_tree = cfind(dg_path)
    exp_tree = cfind(img_path)
    assert current_tree == exp_tree
    current_txt = dg_path.join('foo.spec').read()
    with open(os.path.join(img_path, 'foo.spec')) as fp:
        exp_txt = fp.read()
    assert current_txt == exp_txt


def assert_spec_version(version, release_parts, milestone):
    spec = Spec()
    spec_version = spec.get_tag('Version')
    spec_release_parts = spec.get_release_parts()
    spec_milestone = spec.get_milestone()

    assert spec_version == version
    assert spec_release_parts == release_parts
    assert spec_milestone == milestone


def norm_changelog(count=1):
    spec = Spec()
    r = re.compile(r"%changelog\n", flags=re.I).split(spec.txt)
    if len(r) > 2:
        raise exception.MultipleChangelog()
    txt, chl = r
    chl, n = re.subn(r'^\* .+\s(\d\S*)$',
                     '* DATE AUTHOR \g<1>',
                     chl,
                     count=count,
                     flags=re.M)
    spec._txt = txt + '%changelog\n' + chl
    spec.save()
