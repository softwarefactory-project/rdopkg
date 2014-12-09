hacking rdopkg
==============

Hello, dear stranger who wishes to make rdopkg better. This file aims to get
you started hacking quickly.

Note that certain changes related to update files must be done in rdoupdate
library. 

git repo
--------

Sources are hosted at github:

    git clone https://github.com/redhat-openstack/rdopkg

Submit pull requests.

requirements
------------

Check out `requirements.txt` or `Requires:` in .spec file to see which python
modules you need.

One of them is `rdoupdate` module used for parsing update files:

    git clone http://github.com/yac/rdoupdate.git
    cd rdoupdate
    python setup.py develop --user

For development, I suggest installing both rdopkg and required rdoupdate like
this:
    
    python setup.py develop --user


file layout
-----------

Top level stuff you should know about:

    ├── bsources/     <- internal build sources for rdoupdate (brew, copr-jruzicka)
    ├── doc/          <- man pages/docs in asciidoc
    ├── rdopkg/       <- actual python sources
    ├── rdopkg.spec   <- .spec file to build RPM - don't touch unless asked to
    └── tests/        <- unit tests!!11one1 run by calling `py.test`


sources layout
--------------

Bellow is the full source tree at the time of writing with points into most
interesting files: 

    rdopkg
    ├── __init__.py         <- version is here, don't touch
    ├── action.py
    ├── actionmods          <- reusable modules containing the low level
    │   ├── __init__.py        functionality needed in rdopkg actions;
    │   ├── copr.py            feel free to add your own
    │   ├── nightly.py
    │   ├── pushupdate.py
    │   ├── reviews.py
    │   └── update.py
    ├── actions.py          <- this is basically an imperative config file that
    ├── conf.py                defines actions' interface and logic - please
    ├── const.py               don't put complex code here!
    ├── core.py
    ├── exception.py        <- nova-style exceptions, add as needed
    ├── gerrit
    │   ├── __init__.py
    │   ├── filters.py
    │   ├── reviews.py
    │   └── ssh.py
    ├── guess.py            <- some hardcore automagic guessing happens here
    ├── helpers.py
    ├── shell.py            <- CLI related logic here
    └── utils               <- some generic cool stuffs here, see how it's
        ├── __init__.py        used throughout rdopkg
        ├── cmd.py          <- use run() and git() to interact with the world
        ├── exception.py
        ├── log.py 
        ├── specfile.py     <- lots of .spec editation magic here
        └── terminal.py


actions.py
----------

Looking at this file for a while should give you a good idea how everything
works.

When defining a new action or modifying a behaviour of existing one, you'll
need to edit this file. `ACTIONS` hyperstructure defines entire rdopkg
interface and highest-level flow of actions. Each action function should be
idempotent because it's possible to re-run last action step by `rdopkg -c` on
failure/interrupt.

Action name directly maps to python functions in `actions.py`. Note that
dictionary of persistent values much like `ENV` is stored between action steps
and these are automatically passed to action functions based their signature
(expected arguments). When an action function returns a dictionary, the
global action dictionary is updated with returned values, allowing state to be
stored between steps. That way, functions can be used in rdopkg interface
without redundant definitions (function signature is sufficient) but also by
importing them from rdopkg module and calling them with custom parameters.

As an example, `get_package_env` action function detects package environment
and saves it in the action dictionary by returning a dict with detected
values. `patches_branch` is detected using `guess` module and returned.
Following action functions such as `update_patches` require `patches_branch`
argument which is passed to them from the action dictionary by the action flow
logic @ `action.py`.

You might get surprised by weirdness of action logic but it allows simple and
reusable way of representing multi-step action and mapping them to python
code. If you'd like to change this aspect of rdopkg, I strongly suggest
discusing it with `jruzicka`. He has long answers for questions such as:

* Why flat module instead of mighty OOP classes?
* Why strings-mapped-to-functions instead of referencing functions directly?
* Why action abstractions instead of pure python code?
* Why is action a tree instead of a simple flat list?
* Isn't `actions.py` too big? (YES, but...)


unit tests
----------

If you're doing non-trivial change, I strongly suggest adding unit tests.

Either way, make sure *existing unit tests pass* after your change by running

    py.test

until automatic gating is done on the repo.


update them man pages
---------------------

`grep doc/*.ronn` for keywords relevant to your change and update them if
needed. Documenting new functionality sounds like a good idea, too.

Captain Obvious out.


submitting your c0dez
---------------------

Please use `git review` to submit your patches instead of `git push` unless
you're fixing something trivial like typo.

Workflow:

    git checkout -b some-fix origin/master
    # setup gerrit - adds hook to append commit messages with Change-Id
    git review -s
    # EDIT ALL THE CODEZ
    git commit
    git review

After that, link to gerrit is printed where the rest of the battle will occur.
If you need to submit multiple commits, that's OK. If you need to change your
patch after -1 or so:

    git fetch origin
    git checkout some-fix
    git rebase origin/master
    # FIX ALL THE NITPICKS
    git commit -a
    git review

After that, poke `jruzicka` on IRC to accelerate the review.
