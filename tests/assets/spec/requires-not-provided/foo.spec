%global milestone .0rc2

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:             foo
Epoch:            1
Version:          1.2.3
Release:          0.3
Summary:          Some package, dude

Group:            Development/Languages
License:          ASL 2.0
URL:              http://pypi.python.org/pypi/%{name}
Source0:          http://pypi.python.org/packages/source/f/%{name}/%{name}-%{version}.tar.gz

BuildArch:        noarch
BuildRequires:    python-setuptools
BuildRequires:    python2-devel

Requires:         python-argparse == 42:1.2.3
Requires:         python-iso8601 = 1.2.3
Requires:         python3-prettytable
Requires:         %{name}-api = %{epoch}:%{version}-%{release}

%description
This is foo! This is foo! This is foo! This is foo! This is foo! This is foo!
This is foo! This is foo! This is foo!

%prep
%setup -q

# We provide version like this in order to remove runtime dep on pbr.
sed -i s/REDHATNOVACLIENTVERSION/%{version}/ novaclient/__init__.py

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}


%files
%doc README.rst
%{_bindir}/foo

%package api
Summary: The Test API

%description api
%{description}

%files api
%doc README.rst LICENSE
%if 0%{?with_doc}
%doc doc/build/html/man/%{service}-api.html
%endif
%{_bindir}/%{service}-api
%{_bindir}/%{service}-wsgi-api
%{_unitdir}/openstack-%{service}-api.service
%if 0%{?with_doc}
%{_mandir}/man1/%{service}-api.1.gz
%endif


%changelog
* Mon Apr 07 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.3-42
- Update to upstream 1.2.3

* Tue Mar 25 2014 Jakub Ruzicka <jruzicka@redhat.com> 1.2.2-1
- Update to upstream 1.2.2
