"""
Utility actions module.
"""

from rdopkg.conf import cfg, cfg_files
from rdopkg import exception
from rdopkg.actionmods import doctor as _doctor
from rdopkg.utils import log
from rdopkg import helpers


def status():
    raise exception.InternalAction(action='status')


def conf():
    if cfg_files:
        log.info("Following config files were read:")
        helpers.print_list(cfg_files)
    else:
        log.info("No rdopkg config files found, using default config:")
    log.info("")
    for item in cfg.items():
        log.info("%s: %s" % item)


def actions():
    raise exception.InternalAction(action='actions')


def autocomplete():
    try:
        import argcomplete
        print("argcomplete module is available.")
    except ImportError:
        print(
            "You're missing the argcomplete python module. "
            "Install it using\n\n"
            "    # yum install -y python-argcomplete\n\n"
            "or\n\n"
            "    # pip install argcomplete\n\n"
            "and run `rdopkg autocomplete` again.")
        return
    print('')
    print(
        "Make sure following line is somewhere in your bash config:\n\n"
        '    eval "$(register-python-argcomplete rdopkg)"\n\n'
        "For zsh, you need bashcompinit, see https://github.com/kislyuk/"
        "argcomplete/issues/10#issuecomment-19369876")


def doctor():
    _doctor.can_haz_doctor()
