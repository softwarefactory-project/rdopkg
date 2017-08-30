%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

# Python3 support for Fedora 24+
%if 0%{?fedora} >= 24
%global with_python3 1
%endif

Name:             rdopkg
Version:          0.45.0
Release:          1%{?dist}
Summary:          RPM packaging automation tool

Group:            Development/Languages
License:          ASL 2.0
URL:              https://github.com/softwarefactory-project/rdopkg/
Source0:          https://pypi.python.org/packages/source/r/%{name}/%{name}-%{upstream_version}.tar.gz

BuildArch:        noarch

%description
rdopkg is a tool for automating RPM packaging tasks such as managing patches,
updating to a new version and much more.

Although it contains several RDO-specific actions, most of rdopkg
functionality can be used for any RPM package following conventions
described in the rdopkg manual.

%package -n python2-rdopkg
Summary:          RPM packaging automation tool
%{?python_provide:%python_provide python2-rdopkg}

Provides:         rdopkg == %{version}-%{release}

BuildRequires:    python2-devel
BuildRequires:    python-setuptools
BuildRequires:    python-pbr
BuildRequires:    PyYAML
BuildRequires:    git
# for documentation
BuildRequires:    asciidoc

Requires:         python-bunch
Requires:         python-future
Requires:         python2-koji
Requires:         python-paramiko
Requires:         python-pbr
Requires:         python-pymod2pkg >= 0.2.1
Requires:         pyOpenSSL >= 16.2.0
Requires:         python-requests
Requires:         python-setuptools
Requires:         python-six
Requires:         PyYAML
Requires:         git-core
Requires:         git-review
# optional but recommended
Requires:         python-blessings


%description -n python2-rdopkg
rdopkg is a tool for automating RPM packaging tasks such as managing patches,
updating to a new version and much more.

Although it contains several RDO-specific actions, most of rdopkg
functionality can be used for any RPM package following conventions
described in the rdopkg manual.


%if 0%{?with_python3}
%package -n python3-rdopkg
Summary:          RPM packaging automation tool
%{?python_provide:%python_provide python3-rdopkg}

BuildRequires:    python3-devel
BuildRequires:    python3-setuptools
BuildRequires:    python3-pbr
BuildRequires:    python3-PyYAML

Requires:         python3-future
Requires:         python3-koji
Requires:         python3-paramiko
Requires:         python3-pbr
Requires:         python3-pymod2pkg >= 0.2.1
Requires:         python3-pyOpenSSL >= 16.2.0
Requires:         python3-requests
Requires:         python3-setuptools
Requires:         python3-six
Requires:         python3-PyYAML
Requires:         git-core
Requires:         git-review
# optional but recommended
Requires:         python3-blessings

%description -n python3-rdopkg
rdopkg is a tool for automating RPM packaging tasks such as managing patches,
updating to a new version and much more.

Although it contains several RDO-specific actions, most of rdopkg
functionality can be used for any RPM package following conventions
described in the rdopkg manual.
%endif


%prep
%autosetup -n %{name}-%{upstream_version} -S git

# We handle requirements ourselves, pkg_resources only bring pain
rm -rf requirements.txt test-requirements.txt

%build
%py2_build

%if 0%{?with_python3}
%py3_build
%endif

%install
%if 0%{?with_python3}
%py3_install
mv %{buildroot}%{_bindir}/rdopkg %{buildroot}%{_bindir}/rdopkg-%{python3_version}
ln -s ./rdopkg-%{python3_version} %{buildroot}%{_bindir}/rdopkg-3
%endif

%py2_install
ln -s ./rdopkg %{buildroot}%{_bindir}/rdopkg-%{python2_version}
ln -s ./rdopkg %{buildroot}%{_bindir}/rdopkg-2

# docs use asciidoc because rst is ugly
make doc

# man pages
install -d -m 755 %{buildroot}%{_mandir}/man{1,7}
install -p -m 644 doc/man/*.1 %{buildroot}%{_mandir}/man1/
install -p -m 644 doc/man/*.7 %{buildroot}%{_mandir}/man7/

%files -n python2-rdopkg
%doc README.md
%doc doc/*.adoc doc/html
%license LICENSE
%{_bindir}/rdopkg
%{_bindir}/rdopkg-2
%{_bindir}/rdopkg-%{python2_version}
%{python2_sitelib}/rdopkg
%{python2_sitelib}/*.egg-info
%{_mandir}/man1/rdopkg*
%{_mandir}/man7/rdopkg*

%if 0%{?with_python3}
%files -n python3-rdopkg
%doc README.md
%doc doc/*.adoc doc/html
%license LICENSE
%{_bindir}/rdopkg-3
%{_bindir}/rdopkg-%{python3_version}
%{python3_sitelib}/rdopkg
%{python3_sitelib}/*.egg-info
%endif


%changelog
* Wed Aug 30 2017 Jakub Ružička <jruzicka@redhat.com> 0.45.0-1
- fix: Fix rdo_projects.py example to work with latest rdoinfo
- fix: Remove obsolete run_tests.sh
- fix: Use absolute path for base_path when not using local_repo_path
- fix: cbsbuild: fix compatibility with Koji 1.13
- fix: core: only load state file on --continue
- fix: patch: format-patches with a standard abbrev setting
- fix: restore proper --continue functionality
- fix: show nice message on no distgit changes and unbreak gate
- spec: add Python 3 package
- spec: add docstrings to some methods
- spec: improve unicode support
- spec: properly expand macros defined in .spec file
- tests: Add a rdopkg fix scenario - no changelog update
- tests: Additional test for --abort clears rdopkg state file
- tests: add rdopkg fix revert everything scenario
- tests: enable python 3 testing
- tests: fix whitespace to make pycodestyle happy
- tests: speed up findpkg integration test
- tests: use tox to setup and run tests
- doc: Update MANIFEST.in
- doc: update HACKING.md for new test setup

* Thu Aug 24 2017 Jakub Ruzicka <jruzicka@redhat.com> 0.44.2-2
- Add Python 3 support with python3-rdopkg

* Wed Jul 26 2017 Jakub Ruzicka <jruzicka@redhat.com> 0.44.2-1
- Use absolute path for repo_path

* Tue Jul 25 2017 Jakub Ruzicka <jruzicka@redhat.com> 0.44.1-1
- setup.py: removed versioned requires breaking epel7
- Add pbr to requirements.txt

* Wed Jul 19 2017 Jakub Ruzicka <jruzicka@redhat.com> 0.44.0-1
- Update to 0.44.0
- Add BDD feature tests using python-behave
- Add options to specify user and mail in changelog entry
- Add support for buildsys-tags in info-tags-diff
- Adopt pbr for version and setup.py management
- Avoid prompt on non interactive console
- Avoid test failure due to git hooks
- Fix linting
- Fix output of info-tags-diff for new packages
- Improve changelog handling
- Improve patches_ignore detection
- Migrate to softwarefactory-project.io
- Python 3 compatibility fixes
- allow patches remote and branch to be set in git config
- core: refactor unreasonable default atomic=False
- distgit: Use NVR for commit title for multiple changelog lines
- distgit: new -H/--commit-header-file option
- document new-version's --bug argument
- guess: return RH osdist for eng- dist-git branches
- make git.config_get behave more like dict.get
- new-version: handle RHCEPH and RHSCON products
- patch: new -B/--no-bump option to only sync patches
- pkgenv: display color coded hashes for branches
- refactor: merge legacy rdopkg.utils.exception
- specfile: fix improper naming: get_nvr, get_vr
- tests: enable nice py.test diffs for common test code

* Thu Mar 30 2017 Jakub Ruzicka <jruzicka@redhat.com> 0.43-1
- Update to 0.43
- new-version: allow fully unattended runs
- new-version: re-enable reqdiff
- new-version: don't write patches_base for prefixed tags
- patch: improve new/old patches detection
- patch: new --changelog option
- patch: only create one commit
- update-patches: deprecate in favor of `rdopkg patch`
- pkgenv: don't query rdoinfo for obsolete information
- shell: allow passing action description
- specfile: raise when missing rpm lib in expand_macro()
- tests: increase unit test coverage
- tests: add findpkg integration tests to run_tests.sh
- tests: skip rpm test when rpm module isn't available
- tests: remove old test assets
- tests: run_tests.sh: actually fail on test failure
- cbsbuild: fix cbsbuild command failure
- dist: add pytest to test-requirements.txt
- distgit: better handling for patches_base and ignore
- distgit: correctly use -f/--force option
- doc: add virtualenv howto to HACKING and README
- doc: add documentation on how patches_base is calculated
- doc: improve docs for new-sources
- man: give example for patches_ignore
- guess: handle "VX.Y.Z" Git tags
- pep8 cleanup 

* Tue Nov 22 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.42-1
- Update to 0.42
- Counter past %{?milestone} bug
- findpkg: new command to easily find single package
- specfile: extend BuildArch sanity check to %%autosetup
- specfile: add a sanity check for double # patches_base
- tag-patches: ignore RPM Epoch
- get-source: unbreak after defaults change
- reqcheck: add --spec/-s output for pasting
- pkgenv: show patches apply method

* Tue Nov 08 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.41.4-1
- Update to 0.41.4
- Fixed -c argument parsing
- Evade pyton 2.7.5 regex bug on CentOS 7.2

* Fri Oct 21 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.41.3-1
- Update to 0.41.3
- info: reintroduce lost info and info-diff-tags actions
- tag-patches: fix recommended "push" action
- Make --version work again

* Thu Oct 20 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.41.2-1
- Update to 0.41.2
- Bugfix release that attempts to fix setup.py yet again

* Thu Oct 20 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.41.1-1
- Update to 0.41.1
- Bugfix release that adds rdopkg.actions to setup.py

* Wed Oct 19 2016 Jakub Ruzicka <jruzicka@redhat.com> 0.41-1
- Update to 0.41
- patch: fix milestone handling and cover with unit tests
- Fix macro expansion when redefining macros
- Nuke python-parsley requirement
- actions: add "tag-patches" command
- refactor: split actions.py into action modules
- doc: rename asciidoc files from ".txt" to ".adoc"
- doc: update HACKING.md

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
- update-patches: update the "%%commit" macro
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
