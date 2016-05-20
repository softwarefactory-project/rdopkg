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

    git clone https://github.com/openstack-packages/rdopkg
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


## The Manual

Exhaustive `rdopkg` manual is available, you can:

 * not read it online ATM as we're migrating... [sorry about that](https://github.com/openstack-packages/rdopkg/issues/65)
 * read its nice source: [doc/rdopkg.1.txt](doc/rdopkg.1.txt)
 * run `man rdopkg` if you installed from RPM

You might also be interested in
[RDO packaging guide](https://www.rdoproject.org/documentation/rdo-packaging)
which contains some examples of `rdopkg` usage and more.


## Bugs

Please use the
[github Issues](https://github.com/openstack-packages/rdopkg/issues)
to report bugs. I usually fix them within days.
