import os
import py
import shutil

from rdopkg.utils.cmd import git


ASSETS_DIR = 'tests/assets'


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
        git('commit', '-m', 'Initial import')
    return dist_path


def prep_patches_branch():
    git('checkout', '--orphan', 'master-patches')
    f = open('foofile', 'w')
    f.write("#not really a patch\n")
    f.close()
    git('add', 'foofile')
    git('commit', '-m', 'Create this test branch')
    git('tag', '1.2.3')
    git('checkout', 'master')


def _do_patch(fn, content, msg):
    f = open(fn, 'w')
    f.write(content)
    f.close()
    git('add', fn)
    git('commit', '-m', msg)


def add_patches(extra=False, filtered=False):
    git('checkout', 'master-patches')
    if extra:
        _do_patch('foofile', "#meh\n", 'Look, excluded patch')
        _do_patch('foofile', "#nope\n", 'Yet another excluded patch')
    _do_patch('foofile', "#huehue, change\n", 'Crazy first patch')
    if filtered:
        _do_patch('foofile', "#fix ci\n", 'DROP-IN-RPM: ci fix')
        _do_patch('foofile', "#and now for real\n", 'DROP-IN-RPM: moar ci fix')
    _do_patch('foofile', "#lol, another change\n", 'Epic bugfix of doom MK2')
    if filtered:
        _do_patch('foofile', "#oooops\n", 'DROP-IN-RPM: even moar ci fix')
    git('checkout', 'master')


def assert_distgit(dg_path, img_dg):
    img_path = distgit_path(img_dg)
    current_tree = cfind(dg_path)
    exp_tree = cfind(img_path)
    assert current_tree == exp_tree
    current_txt = dg_path.join('foo.spec').read()
    exp_txt = open(os.path.join(img_path, 'foo.spec')).read()
    assert current_txt == exp_txt
