from behave import *
import os
from rdopkg import helpers
from rdopkg.utils.cmd import run, git
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


class DistgitManager(object):
    def __init__(self, name, path=None):
        self.name = name
        self.path = path or name

    def create_sample(self):
        print(os.getcwd())
        assert not os.path.exists(self.path)
        os.makedirs(self.path)
        with helpers.cdir(self.path):
            spec = specfile.Spec(
                fn='%s.spec' % self.name,
                txt=SAMPLE_SPEC)
            spec.set_tag('Name', self.name)
            spec.save()
            git('init', log_cmd=False)
            git('add', '.', log_cmd=False)
            git('commit', '-m', 'Initial import', log_cmd=False)


def current_commit():
    # TODO: probably put this to Spec parser for convenience
    return git('rev-parse', 'HEAD', log_cmd=False)


@given('a temporary directory')
def step_impl(context):
    context.tempdir = tempfile.mkdtemp(prefix='rdopkg-feature-test-')
    os.chdir(context.tempdir)


@given('a distgit')
def step_impl(context):
    context.execute_steps(u'Given a temporary directory')
    dg = DistgitManager('foo-bar')
    dg.create_sample()
    context.distgitdir = os.path.abspath(dg.path)
    os.chdir(context.distgitdir)
    # collect .spec state to compare against after actions
    spec = specfile.Spec()
    context.old_changelog_entry = spec.get_last_changelog_entry()
    context.old_commit = current_commit()


@then('.spec file doesn\'t contain patches_base')
def step_impl(context):
    spec = specfile.Spec()
    assert spec.get_patches_base() == (None, 0)


@then('.spec file tag {tag} is "{value}"')
def step_impl(context, tag, value):
    spec = specfile.Spec()
    assert spec.get_tag(tag) == value


@then('.spec file has new changelog entry with {n:n} lines')
def step_impl(context, n):
    spec = specfile.Spec()
    entry = spec.get_last_changelog_entry()
    assert len(entry[1]) == n
    assert entry != context.old_changelog_entry


@then('new commit was created')
def step_impl(context):
    assert current_commit() != context.old_commit

