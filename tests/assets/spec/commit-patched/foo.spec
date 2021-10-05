Name:             foo
Epoch:            1
Version:          1.2.3
Release:          42%{?dist}
Summary:          Some package, dude

Group:            Development/Languages
License:          ASL 2.0
URL:              http://pypi.python.org/pypi/%{name}
Source0:          http://pypi.python.org/packages/source/f/%{name}/%{name}-%{version}.tar.gz

%global commit 86a713c35718520cb3b681260182a8388ac809f3

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

# Insert git commit so that it'll show up in `foo --version`
echo "version = '%{commit}'" >> version.py

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
