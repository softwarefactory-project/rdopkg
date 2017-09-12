# rdopkg

`rdopkg` is an RPM packaging automation tool. It provides automation for
package maintenance including git-based patches management and automagic
rebases to new upstream versions with nice changelogs and commit
messages. It also contains various functionality we needed for
[RDO](https://www.rdoproject.org/) packaging, such as advanced
`requirements.txt` management for python projects.

`rdopkg` is **under constant development**, serving mainly the needs of the
mighty [RDO](https://www.rdoproject.org/) packager-warriors, but it strives to
help all RPM packagers.

Generic
[distgit] (https://www.rdoproject.org/documentation/rdo-packaging/#dist-git)
and patches management functionality and conventions provided by `rdopkg`
proved to be efficient way of packaging fast-moving upstream projects with
minimal human effort.

In order to make this functionality conveniently available for packagers, I'm
slowly yet steadily (re)factoring and refining `rdopkg` features into
reusable modules with a grand goal of creating modular packaging tools
framework. This goal is described in
[pwnpkg](https://github.com/yac/pwnpkg) and you should read it if you're
interested in writing you own packaging tools such as new
`fedpkg`/`copr-cli` we deserve.


## Installation


### from Fedora/EPEL repos (default)

`rdopkg` is available on **Fedora 25** and newer:

    dnf install rdopkg

On CentOS/RHEL 7, `rdopkg` is available from
[EPEL](https://fedoraproject.org/wiki/EPEL).

On **CentOS 7**:

    yum install epel-release
    yum install rdopkg

On **RHEL 7**:

    yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
    yum install rdopkg


### from source

If you want to hack `rdopkg` or just have the latest fixes without waiting for
next release, I suggest using the git repo directly:

    git clone https://github.com/softwarefactory-project/rdopkg
    cd rdopkg
    python setup.py develop --user

You may set the preference over `rdopkg` RPM by correctly positioning
`~/.local/bin/rdopkg` in your `$PATH`.

Or you can use virtualenv to avoid conflicts with RPM:

    git clone https://github.com/softwarefactory-project/rdopkg
    cd rdopkg
    virtualenv --system-site-packages ~/rdopkg-venv
    source ~/rdopkg-venv/bin/activate
    python setup.py develop
    ln `which rdopkg` ~/bin/rdopkg-dev

    rdopkg-dev --version

Required python modules are listed in
[requirements.txt](requirements.txt) and also in
[rdopkg.spec](https://src.fedoraproject.org/rpms/rdopkg/blob/master/f/rdopkg.spec) as
RPM Requires.


### from PyPI

For your convenience, `rdopkg` is also available from the Cheese
Shop. This should come in handy especially if you want to reuse `rdopkg` as
a module.

    pip install rdopkg

Note that you need to have python2-rpm(resp. python3-rpm) package installed in
order for RPM macro related featuers to work as it isn't available from
PyPI.


## The Manual

Exhaustive `rdopkg` manual is available, you can:

 * read it nicely rendered on github: [rdopkg manual](https://github.com/softwarefactory-project/rdopkg/blob/master/doc/rdopkg.1.adoc)
 * run `man rdopkg` if you installed from RPM
 * render it to HTML/man using `make doc`

You might also be interested in
[RDO packaging guide](https://www.rdoproject.org/documentation/rdo-packaging)
which contains some examples of `rdopkg` usage and more.


## Bugs

Please use the
[github Issues](https://github.com/softwarefactory-project/rdopkg/issues)
to report bugs. I usually fix them within days.
