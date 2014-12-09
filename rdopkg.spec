Name:             rdopkg
Version:          0.22
Release:          1%{?dist}
Summary:          RDO packaging automation tool

Group:            Development/Languages
License:          ASL 2.0
URL:              https://github.com/redhat-openstack/rdopkg.git
Source0:          %{name}-%{version}.tar.gz

BuildArch:        noarch

BuildRequires:    python-setuptools
BuildRequires:    python2-devel
BuildRequires:    PyYAML

Requires:         rdopkg-bsources >= %{version}
Requires:         python-rdoupdate >= 0.13
Requires:         python-paramiko
Requires:         python-requests
Requires:         python-setuptools
Requires:         PyYAML
Requires:         git-core
Requires:         git-review
Requires:         koji
# optional but recommended
Requires:         python-blessings


%description
rdopkg is a tool for automating RDO packaging tasks including building and
submitting of new RDO packages.


%package bsources
Summary:         Additional RDO build sources for rdoupdate

Requires:        python-rdoupdate >= 0.13
Requires:        python-beautifulsoup4

%description bsources
This package contains additional rdoupdate build sources used for updating RDO.


%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# man page
install -p -D -m 644 doc/rdopkg.1 %{buildroot}%{_mandir}/man1/rdopkg.1
install -p -D -m 644 doc/rdopkg-adv-patch.7 %{buildroot}%{_mandir}/man7/rdopkg-adv-patch.7
install -p -D -m 644 doc/rdopkg-adv-new-version.7 %{buildroot}%{_mandir}/man7/rdopkg-adv-new-version.7
install -p -D -m 644 doc/rdopkg-adv-coprbuild.7 %{buildroot}%{_mandir}/man7/rdopkg-adv-coprbuild.7

# additional build sources
mkdir -p %{buildroot}%{python_sitelib}/rdoupdate/bsources
cp bsources/*.py %{buildroot}%{python_sitelib}/rdoupdate/bsources/

%files
%doc README.md
%doc doc/rdopkg.1.ronn doc/rdopkg.1.html
%{_bindir}/rdopkg
%{python_sitelib}/rdopkg
%{python_sitelib}/*.egg-info
%{_mandir}/man1/rdopkg.1*
%{_mandir}/man7/rdopkg-adv-*

%files bsources
%{python_sitelib}/rdoupdate/bsources/*.py*

%changelog
* Tue Dec 09 2014 Jakub Ruzicka <jruzicka@redhat.com> 0.22-1
- Open source rdopkg
