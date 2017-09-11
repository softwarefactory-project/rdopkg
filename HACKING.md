hacking rdopkg
==============

Hello, dear stranger who wishes to make rdopkg better. This file aims to get
you started hacking quickly.


git repo
--------

Sources are hosted at softwarefactory-project.org and mirrored to github:

    git clone https://github.com/softwarefactory-project/rdopkg

Submit your changes using

    git review

and optionally poke `jruzicka` on #rdo @ freeendoe IRC to accelerate the
review.


requirements
------------

`requirements.txt` lists all the python modules you need.

For development, I suggest installing rdopkg like this:

    python setup.py develop --user


file layout
-----------

Top level stuff you should know about:

    ├── doc/          <- man pages/docs in asciidoc
    ├── rdopkg/       <- actual python sources
    ├── tests/        <- unit tests - run `tox -e py2-unit` or `py.test`
    └── feature/      <- feature tests - run `tox -e py2-feature` or `behave`


sources layout
--------------

Bellow is the full source tree at the time of writing with points into most
interesting files:

    rdopkg
    ├── __init__.py         <- version is here, don't touch
    ├── action.py
    ├── actionmods          <- reusable modules containing the low level
    │   ├── __init__.py        functionality needed in rdopkg actions;
    │   ├── query.py           feel free to add your own
    │   ...
    ├── actions             <- pluggable action modules
    │   ├── build
    │   │   ├── __init__.py
    │   │   └── actions.py
    │   ├── distgit         <- core rdopkg action module
    │   │   ├── __init__.py <- interface declaration
    │   │   └── actions.py  <- action functions (high level interface)
    │   ├── reqs
    │   │   ├── __init__.py
    │   │   └── actions.py
    │   ...
    ├── cli.py              <- default high level CLI interface
    ├── conf.py
    ├── const.py
    ├── core.py
    ├── exception.py        <- nova-style exceptions, add as needed
    ├── guess.py            <- some hardcore automagic guessing happens here
    ├── helpers.py
    ├── shell.py            <- CLI related logic here
    └── utils               <- some generic cool stuffs here, see how it's
        ├── __init__.py        used throughout rdopkg
        ├── cmd.py          <- use run() and git() to interact with the world
        ├── log.py
        ├── specfile.py     <- lots of .spec editation magic here
        └── terminal.py


action modules
--------------

`rdopkg/actions/` contains action modules which are jruzicka's attempt at
reasonable python plugins. Interface declaration is separated in `__init__.py`
allowing rdopkg to collect all available actions and construct CLI without
loading every single module that could possibly be used. Instead, action code
is imported on demand.

    actions
    └── banana            <- banana action module
        ├── __init__.py   <- interface declaration
        ├── actions.py    <- action functions (entry points)
        ├── foo.py        <- arbitrary codez to import form actions.py
        └── bar.py

Each action module contains `__init__.py:ACTIONS` structure which defines
entire rdopkg interface and highest-level flow of actions. Each action
function should be idempotent because it's possible to re-run last action step
by `rdopkg -c` on failure/interrupt.

Action name directly maps to python functions in `actions.py`. Note that
dictionary of persistent values much like `ENV` is stored between action steps
and these are automatically passed to action functions based on their
signature (expected arguments). When an action function returns a dictionary,
the global action dictionary is updated with returned values, allowing state
to be stored between steps. That way, functions can be used in rdopkg
interface without redundant definitions (function signature is sufficient) but
also by importing them directly from rdopkg module and calling them with
custom parameters.

As an example, `distgit.actions:get_package_env` action function detects
package environment and saves it in the action dictionary by returning a dict
with detected values. `patches_branch` is detected using `guess` module and
returned.  Following action functions such as `update_patches` require
`patches_branch` argument which is passed to them from the action dictionary
by the action flow logic @ `action.py`.

`actions.py` should ideally contain only high level logic with the rest of
code in other modules preferably directly in actiom module submodules, but
that's not the case in the time of writing due to legacy reasons.

Finally, note that some refactoring is expected before action modules
interface is stable, not limited to:

 * include full action documentation in `__init__.py` as opposed of having
   only short string there and the rest in doc/ - that's sure to desync over
   time.
 * other quality of life improvements


unit and feature tests
----------------------

If you're doing non-trivial change, I strongly suggest adding

 * unit tests (tests/) to cover low level functionality
 * feature tests  (feature/) to cover high level behavior

Make sure *existing tests pass* after your change by running

    pip install tox
    tox

They need to pass in order for your change to land.


running from virtualenv
-----------------------

You can setup local testing installation of rdopkg using virtualenv:

    git clone https://github.com/softwarefactory-project/rdopkg
    cd rdopkg
    virtualenv --system-site-packages ~/rdopkg-venv
    source ~/rdopkg-venv/bin/activate
    python setup.py develop
    which rdopkg
    ln `which rdopkg` ~/bin/rdopkg-dev

    rdopkg-dev --version

You should then be able to run `rdopkg-dev` from anywhere and it will use the
version you have in your virtualenv instead of the RPM version

If you want to test what it's like if you don't have `rpm` python module ommit
`--system-site-packages` when creating your virtualenv. The tests should pass
but number of them are skipped when `rpm` and `rpmutil` python modules aren't
available.


update them man pages
---------------------

`grep doc/*.adoc` for keywords relevant to your change and update them if
needed. Documenting new functionality sounds like a good idea, too.

Captain Obvious out.
