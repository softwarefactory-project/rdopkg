#!/usr/bin/env python
import sys

from rdopkg.action import ActionManager
from rdopkg.core import ActionRunner
from rdopkg import shell
from rdopkg import actions


def rdopkg(*cargs):
    aman = ActionManager()
    aman.add_actions_modules(actions)
    runner = ActionRunner(action_manager=aman)
    return shell.run(runner, cargs=cargs)


def main(*cargs):
    sys.exit(rdopkg(*cargs))


if __name__ == '__main__':
    main()
