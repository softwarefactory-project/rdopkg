Name:             foo
Epoch:            1
Version:          1.2.3
Release:          43%{?dist}
Summary:          Some package, dude

Group:            Development/Languages
License:          ASL 2.0
URL:              http://pypi.python.org/pypi/%{name}
Source0:          http://pypi.python.org/packages/source/f/%{name}/%{name}-%{version}.tar.gz

Patch0001: 0001-Crazy-first-patch.patch
Patch0002: 0002-Epic-bugfix-of-doom-MK2.patch
Patch0003: 0003-Extra-patch-1.patch
Patch0004: 0004-Extra-patch-2.patch
Patch0005: 0005-Extra-patch-3.patch

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

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1
%patch0005 -p1

# We provide version like this in order to remove runtime dep on pbr.
sed -i s/REDHATNOVACLIENTVERSION/%{version}/ novaclient/__init__.py

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}


%files
%doc README.rst
%{_bindir}/foo

%changelog
* DATE AUTHOR 1:1.2.3-43
- Extra patch 3
- Extra patch 2
- Extra patch 1

* Mon Apr 07 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.3-42
- Update to upstream 1.2.3

* Tue Mar 25 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.2-1
- Update to upstream 1.2.2
