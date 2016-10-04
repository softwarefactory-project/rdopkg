"""
Package build related actions.
"""


from rdopkg.actions.distgit.actions import FEDPKG
from rdopkg import exception
from rdopkg import guess
from rdopkg.actionmods import cbsbuild
from rdopkg.actionmods import copr as _copr
from rdopkg.actionmods import kojibuild
from rdopkg.utils import log
from rdopkg.utils.cmd import git
from rdopkg.utils.cmd import run
from rdopkg import helpers


def fedpkg_mockbuild(fedpkg=FEDPKG):
    cmd = list(fedpkg) + ['mockbuild']
    run(*cmd, direct=True)


def copr_check(release=None, dist=None):
    osdist = guess.osdist()
    if osdist == 'RHOS':
        helpers.confirm("Look like you're trying to build RHOS package in "
                        "public copr.\nProceed anyway?")
    if not release:
        raise exception.CantGuess(
            what='release',
            why="Specify with -r/--release")

    if not dist:
        builds = guess.builds(release=release)
        for dist_, src in builds:
            if src.startswith('copr/jruzicka'):
                dist = dist_
                log.info("Autodetected dist: %s" % dist)
                break
        if not dist:
            raise exception.CantGuess(
                what='dist',
                why="Specify with -d/--dist")
        return {'dist': dist}


def copr_upload(srpm, fuser=None, skip_build=False):
    if not fuser:
        fuser = guess.fuser()
    if skip_build:
        log.info("Skipping SRPM upload due to -s/--skip-build")
        url = _copr.fpo_url(srpm, fuser)
    else:
        url = _copr.upload_fpo(srpm, fuser)
    return {'srpm_url': url}


def copr_build(srpm_url, release, dist, package, version,
               copr_owner='jruzicka', skip_build=False):
    if skip_build:
        log.info("\nSkipping copr build due to -s/--skip-build")
    else:
        copr = _copr.RdoCoprs()
        copr_name = _copr.rdo_copr_name(release, dist)
        repo_url = copr.get_repo_url(release, dist)
        web_url = copr.get_builds_url(release, dist)
        log.info("\n{t.bold}copr:{t.normal} {owner} / {copr}\n"
                 "{t.bold}SRPM:{t.normal} {srpm}\n"
                 "{t.bold}repo:{t.normal} {repo}\n"
                 "{t.bold}web: {t.normal} {web}".format(
                     owner=copr_owner,
                     copr=copr_name,
                     srpm=srpm_url,
                     repo=repo_url,
                     web=web_url,
                     t=log.term))
        copr.new_build(srpm_url, release, dist, watch=True)


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
