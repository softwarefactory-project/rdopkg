import os
from rdopkg import helpers
import rdopkg.utils.cmd
import rdopkg.utils.git
from rdopkg.utils.git import git_branch
from rdopkg.utils import specfile


SAMPLE_SPEC = u"""
Name:             {name}
Epoch:            1
Version:          {version}
Release:          {release}
Summary:          Amazing {name} package

Group:            Development/Languages
License:          ASL 2.0
URL:              http://pypi.python.org/pypi/%{{name}}
Source0:          http://pypi.python.org/lul/%{{name}}/%{{name}}-%{{version}}.tar.gz

{magic_comments}

BuildArch:        noarch
BuildRequires:    python-setuptools
BuildRequires:    python2-devel

Requires:         python-argparse
Requires:         python-iso8601
Requires:         python-prettytable

%description
{name} is incredibly interesting and useful to all beings in universe.

It's pretty good stuff for a testing package that doesn't even exist.

%prep
%setup -q

%build
%{{__python}} setup.py build

%install
%{{__python}} setup.py install -O1 --skip-build --root %{{buildroot}}

%files
%doc README.rst
%{{_bindir}}/{name}

%changelog
* Mon Apr 23 2017 Jakub Ruzicka <jruzicka@redhat.com> {version}-{release}
- Update to upstream {version}
- Introduce new bugs (rhbz#123456)

* Tue Mar 23 2016 Jakub Ruzicka <jruzicka@redhat.com> 1.2.2-1
- Update to upstream 1.2.2
- Escape macros in %%changelog
- Counter %%{{?milestone}} bug

* Tue Jun 23 2015 Jakub Ruzicka <jruzicka@redhat.com> 1.1.1-1
- Update to upstream 1.1.1
- Lorem Ipsum
- Dolor sit Amet
"""  # noqa


# silent run() by default
def run(*args, **kwargs):
    if 'log_cmd' not in kwargs:
        kwargs['log_cmd'] = False
    return rdopkg.utils.cmd.run(*args, **kwargs)


class SilentGit(rdopkg.utils.git.Git):
    def __call__(self, *args, **kwargs):
        if kwargs.get('log_cmd', None) is None:
            kwargs['log_cmd'] = False
        return super(SilentGit, self).__call__(*args, **kwargs)


# silent git() by default
git = SilentGit()


def do_patch(fn, content, msg):
    f = open(fn, 'a')
    content = rdopkg.utils.cmd.encode(content)
    f.write(content)
    f.close()
    git('add', fn)
    git('commit', '-m', msg)


def add_patches(patches):
    if not patches:
        return
    for pn in patches:
        fn = pn.replace('\s', '_')
        do_patch(fn, pn + '\n', pn)


def add_n_patches(n, patch_name='Test Patch %d'):
    if not n:
        return
    for i in range(1, n + 1):
        pn = patch_name % i
        fn = pn.lower().replace(' ', '_')
        do_patch(fn, pn + '\n', pn)


def create_sample_distgit(name, version='1.2.3', release='1', path=None,
                          magic_comments=None):
    if not path:
        path = name
    assert not os.path.exists(path)
    if "%{?dist}" not in release:
        release = release + "%{?dist}"
    os.makedirs(path)
    if not magic_comments:
        magic_comments = ''
    with helpers.cdir(path):
        txt = SAMPLE_SPEC.format(name=name, version=version, release=release,
                                 magic_comments=magic_comments)
        spec = specfile.Spec(fn='%s.spec' % name, txt=txt)
        spec.set_tag('Name', name)
        spec.save()
        git('init',)
        git('add', '.')
        git('commit', '-m', 'Initial import', isolated=True)
    return os.path.abspath(path)


def create_sample_patches_branch(n=0, patches=None, version_tag=True):
    version = specfile.Spec().get_tag('Version')
    branch = git.current_branch()
    if version_tag:
        git('tag', version, fatal=False, log_fail=False)
    git('checkout', '-b', '%s-patches' % branch)
    add_patches(patches)
    add_n_patches(n, patch_name="Original Patch %d")
    git('checkout', branch)


def create_sample_upstream_new_version(
        new_version, n_patches, n_from_patches_branch,
        version_tag=True):
    branch = rdopkg.utils.git.git.current_branch()
    old_version = specfile.Spec().get_tag('Version')
    git('checkout', '-b', 'upstream', old_version)
    add_n_patches(n_patches,
                  patch_name='Upstream Commit %d')
    for i in range(n_from_patches_branch):
        # emulate upstream patches that were backported
        git('cherry-pick', 'master-patches' + i * '~')
    if version_tag:
        git('tag', new_version)
    git('checkout', branch)
