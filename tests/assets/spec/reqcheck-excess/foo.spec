# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver 3
%else
%global pyver 2
%endif

%global pyver_bin python%{pyver}
%global pyver_sitelib %{expand:%{python%{pyver}_sitelib}}
%global pyver_install %{expand:%{py%{pyver}_install}}
%global pyver_build %{expand:%{py%{pyver}_build}}
# End of macros for py2/py3 compatibility

Name:             foo
Epoch:            2077
Version:          1.2.3
Release:          42%{?dist}
Summary:          Some package, dude

Group:            Development/Languages
License:          ASL 2.0
URL:              http://notreallyavaliddomain.name/foo

BuildArch:        noarch

Source0:          %{name}/%{name}-%{version}.tar.gz

Patch0001: 0001-something.patch
Patch0002: 0002-something-else.patch

BuildRequires:    python-setuptools
BuildRequires:    python2-devel
%if %{pyver} == 2
BuildRequires: PyYAML
BuildRequires: pytz
%else
BuildRequires: python%{pyver}-PyYAML
BuildRequires: python%{pyver}-pytz
%endif


Requires:         python-argparse
Requires:         python-iso8601
Requires:         python-prettytable
Requires:         python-sqlalchemy >=  1.0.10

Requires(pre):    shadow-utils

%description
This is foo! This is foo! This is foo! This is foo! This is foo! This is foo!
This is foo! This is foo! This is foo!

%setup -q


%prep
%setup -q

%patch0001 -p1
%patch0002 -p1

# We provide version like this in order to remove runtime dep on pbr.
sed -i s/REDHATNOVACLIENTVERSION/%{version}/ novaclient/__init__.py

%build
%{__python3} setup.py build

%install
%{__python3} setup.py install -O1 --skip-build --root %{buildroot}


%files
%doc README.rst
%{_bindir}/foo
# hardcoded library path
/usr/lib/share/foo

%changelog
* Mon Apr 07 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.3-42
- Update to upstream 1.2.3
- Oh no, there's a %macro in changelog

* Tue Mar 25 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.2-1
- Update to upstream 1.2.2
