#!/usr/bin/env python
import sys

from . import VERSION
from rdopkg.action import ActionManager
from rdopkg.core import ActionRunner
from rdopkg import shell
from rdopkg import actions


def rdopkg_runner():
    """
    default rdopkg action runner including rdopkg action modules
    """
    aman = ActionManager()
    # assume all actions.* modules are action modules
    aman.add_actions_modules(actions)
    # additional rdopkg action module logic should go here
    return ActionRunner(action_manager=aman)


def rdopkg(*cargs):
    """
    rdopkg CLI interface

    Execute rdopkg action with specified arguments and return
    shell friendly exit code.

    This is the default high level way to interact with rdopkg.

        py> rdopkg('new-version', '1.2.3')

    is equivalent to

        $> rdopkg new-version 1.2.3
    """
    runner = rdopkg_runner()
    return shell.run(runner, cargs=cargs, version=VERSION)


def main():
    """
    rdopkg console_scripts entry point
    """
    cargs = sys.argv[1:]
    sys.exit(rdopkg(*cargs))


if __name__ == '__main__':
    main()
