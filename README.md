# rdopkg

`rdopkg` is RDO packaging tool. It provides automation for modifying,
building and submitting (not only) [RDO](https://openstack.redhat.com) RPM
packages.



## Installation


### from RPM repo (default)

The easiest and recommended way to get rdopkg is use [jruzicka/rdopkg
copr](https://copr.fedoraproject.org/coprs/jruzicka/rdopkg/). The linked
page contains instructions howto enable the repository.

After you've enabled the repo, just

    yum install rdopkg


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

Exhaustive `rdopkg` manual is avalable, you can:

 * [read it online](https://www.rdoproject.org/packaging/rdopkg/rdopkg.1.html)
 * read its nice source: [doc/rdopkg.1.txt](doc/rdopkg.1.txt)
 * run `man rdopkg` if you installed from RPM

You might also be interested in [RDO packaging
guide](https://www.rdoproject.org/packaging/rdo-packaging.html) which contains
some examples of `rdopkg` usage and more.



## Bugs

Please use the github Issues to report bugs. I usually fix them within days.
