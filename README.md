# rdopkg

`rdopkg` is an RPM packaging automation tool. It provides automation for
package maintenance including git-based patches management and automagic
rebases to new upstream versions with nice .spec changes, changelogs and
commit messages for both CLI and CI usage.
It also contains various functionality we needed for
[RDO](https://www.rdoproject.org/) packaging, such as advanced
`requirements.txt` management for python projects and
[rdoinfo](https://github.com/redhat-openstack/rdoinfo) integration.

Generic
[distgit](https://www.rdoproject.org/documentation/intro-packaging/#distgit---where-the-spec-file-lives)
and patches management functionality and conventions provided by `rdopkg`
proved to be efficient way of packaging fast-moving upstream projects with
minimal human effort but without losing control over individual packages.

`rdopkg` is **under constant development**, serving mainly the needs of the
mighty [RDO](https://www.rdoproject.org/) packager-warriors and and their
weapons such as [DLRN](https://github.com/softwarefactory-project/DLRN),
but it strives to help all RPM packagers. For example, see
[how you can manage your RPMs with
rdopkg](https://www.rdoproject.org//blog/2017/03/let-rdopkg-manage-your-RPM-package/).

`rdopkg` uses [software factory](https://softwarefactory-project.io/)
for CI and every commit goes through automatic unit, feature, and integration
testing as well as human reviews.

See [open rdopkg reviews](https://softwarefactory-project.io/r/#/q/status:open+project:rdopkg).

`rdopkg` is fully reusable but the goal of also serving as
packaging CLI tool framework as described in
[pwnpkg](https://github.com/yac/pwnpkg) proved to be out of scope. However,
(not only `jruzicka`'s) rants ignited [rpkg2][] project
which aims to provide exactly that. If you're interested in writing you own
packaging tools such as new `fedpkg`/`copr-cli` we deserve, [rpkg2][] seems
like a good place to start and influence with good ideas.

[rpkg2]: https://pagure.io/rpkg2


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


## The Manual

Exhaustive `rdopkg` manual is available, you can:

 * read it nicely rendered on github: [rdopkg manual](https://github.com/softwarefactory-project/rdopkg/blob/master/doc/rdopkg.1.adoc)
 * run `man rdopkg` if you installed from RPM
 * render it to HTML/man using `make doc`

You might also be interested in
[RDO packaging intro](https://www.rdoproject.org/documentation/intro-packaging/)
which contains some examples of `rdopkg` usage and more.


## Bugs

Please use the
[github Issues](https://github.com/softwarefactory-project/rdopkg/issues)
to report bugs. I usually fix critical bugs within days.
