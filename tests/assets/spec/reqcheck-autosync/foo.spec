Name:             foo
Version:          1.2.3
Release:          42%{?dist}
Summary:          Some package, dude
License:          ASL 2.0

BuildRequires:    python3-setuptools
BuildRequires:    python3-devel
Requires:         python3-to-be-removed1
Requires:         python3-to-be-removed-2
Requires:         python3-to-be-edited-3
Requires:         python3-to-be-edited4 >= 2.0.1
Requires:         python3-to-be-edited5 >= 1.0.10
Requires:         python3-to-be-edited9 #fail
Requires:         python3-to-be-removed11 #fail

PreReq:           is-deprecated

%description
This is foo!
