"""
Package build related actions.
"""


from rdopkg.actions.distgit.actions import FEDPKG
from rdopkg import exception
from rdopkg import guess
from rdopkg.actionmods import cbsbuild
from rdopkg.actionmods import kojibuild
from rdopkg.utils import log
from rdopkg.utils.git import git
from rdopkg.utils.cmd import run
from rdopkg import helpers


def fedpkg_mockbuild(fedpkg=FEDPKG):
    cmd = list(fedpkg) + ['mockbuild']
    run(*cmd, direct=True)


def koji_build():
    if git.branch_needs_push():
        helpers.confirm("It seems local distgit branch needs push. Push "
                        "now?")
        git('push')
    kojibuild.new_build()


def cbs_build(scratch=False):
    if git.branch_needs_push() and not scratch:
        helpers.confirm("It seems local distgit branch needs push. Push "
                        "now?")
        git('push')
    cbsbuild.new_build(profile='cbs', scratch=scratch)
