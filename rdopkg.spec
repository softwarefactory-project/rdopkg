Name:             rdopkg
Version:          0.40
Release:          1%{?dist}
Summary:          RPM packaging automation tool

Group:            Development/Languages
License:          ASL 2.0
URL:              https://github.com/redhat-openstack/rdopkg.git
Source0:          https://pypi.python.org/packages/source/r/%{name}/%{name}-%{version}.tar.gz

BuildArch:        noarch

BuildRequires:    python-setuptools
BuildRequires:    python2-devel
BuildRequires:    PyYAML

Requires:         python-paramiko
Requires:         python-pymod2pkg >= 0.2.1
Requires:         python-requests
Requires:         python-setuptools
Requires:         PyYAML
Requires:         git-core
Requires:         git-review
Requires:         koji
# optional but recommended
Requires:         python-blessings


%description
rdopkg is a tool for automating RPM packaging tasks such as managing patches,
updating to a new version and much more.

Although it contains several RDO-specific actions, most of rdopkg
functionality can be used for any RPM package following conventions
described in the rdopkg manual.


%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# man pages
install -d -m 755 %{buildroot}%{_mandir}/man{1,7}
install -p -m 644 doc/man/*.1 %{buildroot}%{_mandir}/man1/
install -p -m 644 doc/man/*.7 %{buildroot}%{_mandir}/man7/

%files
%doc README.md
%doc doc/*.adoc doc/html
%license LICENSE
%{_bindir}/rdopkg
%{python_sitelib}/rdopkg
%{python_sitelib}/*.egg-info
%{_mandir}/man1
%{_mandir}/man7

%changelog
* Thu Sep 15 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.40-1
- Update to 0.40
- info-tags-diff: new utility action to show rdoinfo tag changes
- patch: fix traceback with no new patches
- pkgenv: fix traceback on unknown gerrit chain
- Fix new-version release tag management
- cbsbuild: make rpm module optional

* Wed Aug 24 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.39-1
- Update to 0.39
- new-version: support X.Y.Z.0MILESTONE releases
- pkgenv: show NVR detected from .spec
- cbsbuild: make koji module optional

* Wed Jul 20 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.38-1
- Update to 0.38

* Thu Jun 02 2016 Haikel Guemar <hguemar@fedoraproject.org> 0.37-2
- Drop deprecated rdoupdate code

* Mon May 23 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.37-1
- Release 0.37
- patchlog: print rhbz numbers
- patch: add rhbz numbers from commits
- patch: Improve parsing of .spec Source attribute
- actions: Do not reset branch if local_patches is set
- Reintroduce new-sources autodetection for RHOSP
- check_new_patches: Do not count commits using the patches_ignore keyword
- README: update links and more
- HACKING.md: correct tests command

* Wed Apr 20 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.36-1
- Release 0.36
- Support new review based workflow with rpmfactory
- patch, new-version: support review workflow
- review-patch, review-spec: new actions

* Fri Mar 04 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.35.1-1
- Update to 0.35.1
- repoman: fix regression on local rdoinfo repo

* Fri Mar 04 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.35-1
- Update to 0.35
- experimental support for patches in gerrit reviews

* Tue Jan 26 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.34-1
- Update to 0.34
- info: support rdoinfo tags/overrides

* Mon Jan 11 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.33-1
- Update to 0.33
- update-patches: support #patches_ignore regex filter

* Fri Oct 16 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.32.1-1
- Update to 0.32.1
- new-version: fix patches branch detection

* Wed Oct 14 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.32-1
- Update to 0.32
- clone: new action to setup RDO package git remotes
- update-patches: smarter .spec patch management

* Fri Oct 02 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.31-1
- Update to 0.31
- new-version: auto --bump-only on missing patches branch
- new-version: only run `fedpkg new-sources` with non-empty sources file
- update-patches: update the "%commit" macro
- patchlog: new action to show patches branch log
- remove unused 'rebase' action

* Tue Aug 11 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.30-1
- Update to 0.30
- spec: require standalone pymod2pkg >= 0.2.1
- log: improve stdout vs stderr logging
- helpers.edit: Clear message about unset $EDITOR
- update-patches: ignore git submodule changes

* Tue Aug 04 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.29.1-1
- Update to 0.29.1
- Handle version_tag_style in check_new_patches()

* Thu Jul 23 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.29-2
- Update package description

* Thu Jul 23 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.29-1
- Update to 0.29
- new-version: support vX.Y.Z version tags
- core: improve state file handling

* Fri Jun 26 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.28.1-1
- Update to 0.28.1
- doc: such documentation, much clarity, wow

* Wed Jun 03 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.28-1
- Update to 0.28
- reqquery: manage dem requirements like a boss

* Mon May 04 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.27.1-1
- Update to 0.27.1
- update-patches: create commit even with only removed patches

* Mon Apr 27 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.27-1
- Update to 0.27
- reqcheck: new action to check for correct Requires

* Mon Mar 30 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.26-1
- Update to 0.26
- query: new action to query RDO package versions
- update: use SSH for update repo
- reqdiff: fix stupid regexp
- new-version: ignore missing requirements.txt diff

* Wed Feb 18 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.25-1
- Update to 0.25
- update: parsable update summary in gerrit topic
- Provide set_colors function to control color output

* Wed Feb 04 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.24-1
- Update to upstream 0.24
- update-patches: support %%autosetup patch apply method
- Require rdoupdate with cbs support

* Thu Jan 22 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.23.1-1
- Update to 0.23.1
- Packaging fixes

* Tue Jan 20 2015 Jakub Ruzicka <jruzicka@redhat.com> 0.23-1
- Update to 0.23
- kojibuild: offer push when needed
- reqdiff: new action & integrated into new-version
- core: fix state file handling and atomic actions

* Tue Dec 09 2014 Jakub Ruzicka <jruzicka@redhat.com> 0.22-1
- Open source rdopkg
