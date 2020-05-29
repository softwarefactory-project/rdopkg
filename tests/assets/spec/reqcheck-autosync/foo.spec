Name:             foo
Version:          1.2.3
Release:          42%{?dist}
Summary:          Some package, dude
License:          ASL 2.0

BuildRequires:    python3-setuptools
BuildRequires:    python3-devel
Requires:         python3-argparse
Requires:         python3-iso8601 >= 2.0.1
Requires:         python3-prettytable
Requires:         python3-osc-lib >= 0.9.1
Requires:         python3-osc-lib-tests
Requires:         python3-oslo-db
Requires:         python3-after-pkg1

PreReq:           is-deprecated

%description
This is foo!
