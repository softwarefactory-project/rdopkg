from behave import *
import os
from rdopkg import helpers
import rdopkg.utils.cmd
from rdopkg.utils import specfile
import tempfile


SAMPLE_SPEC = u"""
Name:             foo
Epoch:            1
Version:          1.2.3
Release:          42%{?dist}
Summary:          Some package, dude

Group:            Development/Languages
License:          ASL 2.0
URL:              http://pypi.python.org/pypi/%{name}
Source0:          http://pypi.python.org/lul/name}/%{name}-%{version}.tar.gz

BuildArch:        noarch
BuildRequires:    python-setuptools
BuildRequires:    python2-devel

Requires:         python-argparse
Requires:         python-iso8601
Requires:         python-prettytable

%description
This is foo! This is foo! This is foo! This is foo! This is foo! This is foo!
This is foo! This is foo! This is foo!

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

%files
%doc README.rst
%{_bindir}/foo

%changelog
* Mon Apr 23 2017 Jakub Ruzicka <jruzicka@redhat.com> 1.2.3-42
- Update to upstream 1.2.3
- Introduce new bugs (rhbz#123456)

* Tue Mar 23 2016 Jakub Ruzicka <jruzicka@redhat.com> 1.2.2-1
- Update to upstream 1.2.2

* Tue Jun 23 2015 Jakub Ruzicka <jruzicka@redhat.com> 1.1.1-1
- Update to upstream 1.1.1
- Lorem Ipsum
- Dolor sit Amet
"""


def run(*args, **kwargs):
    kwargs['log_cmd'] = False
    return rdopkg.utils.cmd.run(*args, **kwargs)


def git(*args, **kwargs):
    kwargs['log_cmd'] = False
    return rdopkg.utils.cmd.git(*args, **kwargs)


def create_sample_distgit(name, path=None):
    if not path:
        path = name
    assert not os.path.exists(path)
    os.makedirs(path)
    with helpers.cdir(path):
        spec = specfile.Spec(
            fn='%s.spec' % name,
            txt=SAMPLE_SPEC)
        spec.set_tag('Name', name)
        spec.save()
        git('init', log_cmd=False)
        git('add', '.', log_cmd=False)
        git('commit', '-m', 'Initial import', log_cmd=False)
    return os.path.abspath(path)


def do_patch(fn, content, msg):
    f = open(fn, 'a')
    f.write(content)
    f.close()
    git('add', fn)
    git('commit', '-m', msg)


def add_n_patches(n, patch_name='Test Patch %d'):
    git('checkout', 'master-patches')
    for i in range(1, n + 1):
        pn = patch_name % i
        do_patch('foofile', pn + '\n', pn)
    git('checkout', 'master')


def create_sample_patches_branch(n):
    version = specfile.Spec().get_tag('Version')
    git('tag', version)
    git('branch', 'master-patches')
    add_n_patches(n, patch_name="Original Patch %d")


def current_commit():
    # TODO: probably put this to Spec parser for convenience
    return git('rev-parse', 'HEAD', log_cmd=False)


@given('a temporary directory')
def step_impl(context):
    context.tempdir = tempfile.mkdtemp(prefix='rdopkg-feature-test-')
    context.old_cwd = os.getcwd()
    os.chdir(context.tempdir)


@given('a distgit')
def step_impl(context):
    name = 'foo-bar'
    context.execute_steps(u'Given a temporary directory')
    context.distgitdir = create_sample_distgit(name)
    os.chdir(context.distgitdir)
    # collect .spec state to compare against after actions
    spec = specfile.Spec()
    context.old_changelog_entry = spec.get_last_changelog_entry()
    context.old_commit = current_commit()


@given('a patches branch with {n:n} patches')
def step_impl(context, n):
    create_sample_patches_branch(n)


@then('.spec file doesn\'t contain patches_base')
def step_impl(context):
    spec = specfile.Spec()
    assert spec.get_patches_base() == (None, 0)


@then('.spec file tag {tag} is "{value}"')
def step_impl(context, tag, value):
    spec = specfile.Spec()
    assert spec.get_tag(tag) == value


@then('.spec file doesn\'t contain new changelog entries')
def step_impl(context):
    entry = specfile.Spec().get_last_changelog_entry()
    assert entry == context.old_changelog_entry


@then('.spec file contains new changelog entry with {n:n} lines')
def step_impl(context, n):
    spec = specfile.Spec()
    entry = spec.get_last_changelog_entry()
    assert len(entry[1]) == n
    assert entry != context.old_changelog_entry


@then('.spec file has {n:n} patches defined')
def step_impl(context, n):
    spec = specfile.Spec()
    assert spec.get_n_patches() == n


@then('new commit was created')
def step_impl(context):
    assert current_commit() != context.old_commit

