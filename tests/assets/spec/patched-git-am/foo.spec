Name:             foo
Epoch:            1
Version:          1.2.3
Release:          42%{?dist}
Summary:          Some package, dude

Group:            Development/Languages
License:          ASL 2.0
URL:              http://pypi.python.org/pypi/%{name}
Source0:          http://pypi.python.org/packages/source/f/%{name}/%{name}-%{version}.tar.gz

# patches_base=+2
Patch0001: 0001-Crazy-first-patch.patch
Patch0002: 0002-Epic-bugfix-of-doom-MK2.patch

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

# Use git to manage patches.
# http://rwmj.wordpress.com/2011/08/09/nice-rpm-git-patch-management-trick/
git init
git config user.email "foo@bar.org"
git config user.name "bob"
git add .
git commit -a -q -m "%{version} baseline"
git am %{patches}

# We provide version like this in order to remove runtime dep on pbr.
sed -i s/REDHATNOVACLIENTVERSION/%{version}/ novaclient/__init__.py

%build
%{__python3} setup.py build

%install
%{__python3} setup.py install -O1 --skip-build --root %{buildroot}


%files
%doc README.rst
%{_bindir}/foo

%changelog
* Mon Apr 07 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.3-42
- Update to upstream 1.2.3

* Tue Mar 25 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.2-1
- Update to upstream 1.2.2
