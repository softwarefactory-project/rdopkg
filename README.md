# rdopkg

`rdopkg` is an RPM packaging automation tool. It provides automation for
package maintenance including git-based patches management and automagic
rebases to new upstream versions. It also contains various functionality we
needed for [RDO](https://www.rdoproject.org/) packaging, such as advanced
`requirements.txt` management for python projects.

`rdopkg` is under constant development, serving the needs of the mighty
[RDO](https://www.rdoproject.org/) packager-warriors.

Generic
[dist-git](https://www.rdoproject.org/packaging/rdo-packaging.html#dist-git)
and patches management functionality and conventions provided by `rdopkg`
proved to be efficient way of packaging fast-moving upstream projects with
minimal human effort. In order to make this functionality conveniently
available for packagers, I'm splitting (and refactoring) the best of `rdopkg`
features into a generic modular packaging tools framework called
[pwnpkg](https://github.com/yac/pwnpkg). Check it out if you are interested in
advanced dist-git patches management, writing you own `*pkg` tool or creating
`fedpkg`/`copr-cli` we deserve.


## Installation


### from RPM repo (default)

The easiest and recommended way to get rdopkg is use [jruzicka/rdopkg
copr](https://copr.fedoraproject.org/coprs/jruzicka/rdopkg/). The linked
page contains instructions howto enable the repository:

    dnf copr enable jruzicka/rdopkg

After you've enabled the repo, just

    dnf install rdopkg

Note that [Fedora review](https://bugzilla.redhat.com/show_bug.cgi?id=1246199)
is underway but not likely to finish before `pwnpkg` split.


### from source

If you want to hack `rdopkg` or just have the latest fixes without waiting for
next release, I suggest using the git repo directly a la

    git clone https://github.com/redhat-openstack/rdopkg
    cd rdopkg
    python setup.py develop --user

Required python modules are listed in
[requirements.txt](requirements.txt) and also in [rdopkg.spec](rdopkg.spec) as
RPM requirements.


### from PyPI

For your convenience, `rdopkg` is also available from the Cheese
Shop. This should come in handy especially if you want to reuse `rdopkg` as
a module.

    pip install rdopkg



## [The Manual](https://www.rdoproject.org/packaging/rdopkg/rdopkg.1.html)

Exhaustive `rdopkg` manual is available, you can:

 * [read it online](https://www.rdoproject.org/packaging/rdopkg/rdopkg.1.html)
 * read its nice source: [doc/rdopkg.1.txt](doc/rdopkg.1.txt)
 * run `man rdopkg` if you installed from RPM

You might also be interested in [RDO packaging
guide](https://www.rdoproject.org/packaging/rdo-packaging.html) which contains
some examples of `rdopkg` usage and more.


## Bugs

Please use the
[github Issues](https://github.com/redhat-openstack/rdopkg/issues)
to report bugs. I usually fix them within days.
