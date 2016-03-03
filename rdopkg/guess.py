import os
import re

import exception
from utils.cmd import run, git
from utils import specfile
from rdopkg.actionmods import rdoinfo
from rdopkg.conf import cfg


def package(default=exception.CantGuess):
    pkg = os.path.basename(os.getcwd())
    if not pkg:
        if default is exception.CantGuess:
            raise exception.CantGuess(what="package",
                                      why="failed to parse current directory")
        else:
            return default
    return pkg


def current_version(default=exception.CantGuess):
    version = None
    try:
        spec = specfile.Spec()
        version, _ = spec.get_patches_base(expand_macros=True)
        if version:
            version, _ = tag2version(version)
        else:
            version = spec.get_tag('Version', expand_macros=True)
        if not version:
            raise exception.CantGuess(msg="got empty .spec Version")
    except Exception as ex:
        if default is exception.CantGuess:
            raise exception.CantGuess(
                what="current package version",
                why=str(ex))
        else:
            return default
    return version


def current_branch(default=exception.CantGuess):
    try:
        branch = git.current_branch()
    except exception.CommandFailed:
        if default is exception.CantGuess:
            raise exception.CantGuess(
                what="branch",
                why="git command failed (not in a git repo?)")
        else:
            return default
    if not branch:
        if default is exception.CantGuess:
            raise exception.CantGuess(what="branch",
                                      why="git command returned no output")
        else:
            return default
    return branch


def tag2version(tag):
    if tag and re.match('^v[0-9]', tag):
        return tag[1:], 'vX.Y.Z'
    return tag, None


def version2tag(version, tag_style=None):
    if tag_style == 'vX.Y.Z':
        return 'v' + version
    return version


def version_tag_style(version=None):
    if not version:
        version = current_version()
    if git.ref_exists('refs/tags/' + version):
        return None
    elif git.ref_exists('refs/tags/v' + version):
        return 'vX.Y.Z'
    return None


def find_patches_branch(distgit, remote):
    pb = '%s/%s-patches' % (remote, distgit)
    if git.ref_exists('refs/remotes/%s' % pb):
        return pb
    parts = distgit.split('-')[:-1]
    while parts:
        pb = '%s/%s-patches' % (remote, '-'.join(parts))
        if git.ref_exists('refs/remotes/%s' % pb):
            return pb
        parts.pop()
    return None


def patches_branch(distgit, pkg=None, osdist='RDO'):
    remotes = ['patches']
    # support legacy remote names
    if osdist == 'RHOS':
        remotes.append('rhos')
    else:
        remotes.append('redhat-openstack')
    # support patches branch in the same remote
    remote = git.remote_of_local_branch(distgit)
    if remote:
        remotes.append(remote)

    special_name = None
    # special case for RDO client stable branches
    if osdist == 'RDO' and pkg and pkg.endswith('client'):
        release = osrelease(distgit, default=None)
        if release:
            special_name = 'stable/%s' % release

    for remote in remotes:
        if special_name:
            pb = '%s/%s' % (remote, special_name)
            if git.ref_exists('refs/remotes/%s' % pb):
                return pb
        else:
            pb = find_patches_branch(distgit, remote)
            if pb:
                return pb

    return '%s/%s-patches' % (remotes[0], distgit)


def upstream_branch():
    remotes = ['upstream', 'openstack']

    for remote in remotes:
        ub = '%s/master' % remote
        if git.ref_exists('refs/remotes/%s' % ub):
            return ub

    return '%s/master' % remotes[0]


def upstream_version(branch=None):
    if not branch:
        branch = upstream_branch()
    if git.ref_exists('refs/remotes/%s' % branch):
        vtag = git.get_latest_tag(branch)
        if not vtag:
            return None
        version, _ = tag2version(vtag)
        return version
    return None


def user():
    user = git('config', 'user.name', log_cmd=False, fatal=False)
    if not user:
        raise exception.CantGuess(what="user name",
                                  why='git config user.name not set')
    return user.decode('utf-8')


def email():
    email = git('config', 'user.email', log_cmd=False, fatal=False)
    if not email:
        raise exception.CantGuess(what="user email",
                                  why='git config user.email not set')
    return email


def fuser():
    return os.environ['USER']


def _get_rdoinfo():
    inforepo = rdoinfo.get_default_inforepo()
    inforepo.init(force_fetch=False)
    return inforepo.get_info()


def osreleasedist_rdoinfo(branch):
    info = _get_rdoinfo()
    for rls in info['releases']:
        for repo in rls['repos']:
            if repo['branch'] == branch:
                return rls['name'], repo['name']
    return None, None


def osreleasedist(branch=None, default=exception.CantGuess):
    if branch is None:
        try:
            branch = current_branch()
        except exception.CantGuess as ex:
            if default is exception.CantGuess:
                raise exception.CantGuess(what="release",
                                          why=ex.kwargs['why'])
            else:
                return default

    rls, dist = osreleasedist_rdoinfo(branch)
    if rls:
        return rls, dist

    if default is exception.CantGuess:
        raise exception.CantGuess(what="release",
                                  why="unknown branch '%s'" % branch)
    else:
        return default


def osrelease(branch=None, default=exception.CantGuess):
    rls, _ = osreleasedist(branch=branch, default=(default, None))
    return rls


def dist(branch=None, default=exception.CantGuess):
    _, dist = osreleasedist(branch=branch, default=(None, default))
    return dist


def builds(release):
    info = _get_rdoinfo()
    b = []
    for rls in info['releases']:
        if rls['name'] != release:
            continue
        for repo in rls['repos']:
            bs = repo.get('buildsys')
            if not bs:
                continue
            name = repo['name']
            b.append((name,bs))
        break
    return b


def osdist(branch=None):
    if branch is None:
        branch = current_branch(default='')
    if branch.startswith('rhos-') or branch.startswith('rh-'):
        return 'RHOS'
    return 'RDO'
