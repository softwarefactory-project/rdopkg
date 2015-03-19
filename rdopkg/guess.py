import os
import re

import exception
from utils.cmd import run, git
from rdopkg.actionmods import rdoinfo
from rdopkg.conf import cfg


OS_RELEASES = [
    ('austin', None),
    ('bexar', None),
    ('cactus', None),
    ('diablo', None),
    ('essex', 1),
    ('folsom', 2),
    ('grizzly', 3),
    ('havana', 4),
    ('icehouse', 5),
    ('juno', 6),
    ('kilo', 7),
]

# XXX: moving part (will need update on new Fedora release)
FEDORA_MASTER = 'f22'


def os_release_name(n):
    names = [name for name, ver in OS_RELEASES if ver == n]
    if not names:
        return None
    return names[0]


def package(default=exception.CantGuess):
    pkg = os.path.basename(os.getcwd())
    if not pkg:
        if default is exception.CantGuess:
            raise exception.CantGuess(what="package",
                                      why="failed to parse current directory")
        else:
            return default
    return pkg


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


def osrelease_internal(branch):
    _branch = branch
    if branch == 'master':
        _branch = FEDORA_MASTER
    m = re.match(r'f(\d+)$', _branch)
    if m:
        # XXX: RDO/Fedora dark magic: f19 -> grizzly, f20 -> havana, ...
        fedn = int(m.group(1))
        ver = fedn - 16
        name = os_release_name(ver)
        if name:
            return name

    for name, _ in OS_RELEASES:
        m = re.search(r'\b%s\b' % name, branch, re.I)
        if m:
            return name
    for name, ver in OS_RELEASES:
        if not ver:
            continue
        m = re.search(r'\b(%d)\.\d+(?:\.\d+)*\b' % ver, branch)
        if m:
            return name
    return None


def osrelease_rdoinfo(branch):
    info = _get_rdoinfo()
    for rls in info['releases']:
        for repo in rls['repos']:
            if repo['branch'] == branch:
                return rls['name']
    return None


def osrelease(branch=None, default=exception.CantGuess):
    if branch is None:
        try:
            branch = current_branch()
        except exception.CantGuess as ex:
            if default is exception.CantGuess:
                raise exception.CantGuess(what="release",
                                          why=ex.kwargs['why'])
            else:
                return default

    rls = osrelease_rdoinfo(branch)
    if rls:
        return rls
    rls = osrelease_internal(branch)
    if rls:
        return rls

    if default is exception.CantGuess:
        raise exception.CantGuess(what="release",
                                  why="unknown branch '%s'" % branch)
    else:
        return default


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


# XXX: obsolete, remove if really unused
def dist(branch=None, default=exception.CantGuess):
    if branch is None:
        try:
            branch = current_branch()
        except exception.CantGuess as ex:
            if default is exception.CantGuess:
                raise exception.CantGuess(what="dist",
                                          why=ex.kwargs['why'])
            else:
                return default

    m = re.search(r'\brhel-?(\d+)\b', branch, re.I)
    if m:
        return 'rhel-' + m.group(1)
    m = re.search(r'\be(?:pe)?l-?(\d+)\b', branch, re.I)
    if m:
        return 'epel-' + m.group(1)
    _branch = branch
    if branch == 'master':
        _branch = FEDORA_MASTER
    m = re.search(r'\bf(?:edora)?-?(\d+)\b', _branch, re.I)
    if m:
        fedn = int(m.group(1))
        # XXX: RDO provides packages for Fedora N-1
        fedn -= 1
        return 'fedora-%d' % fedn

    if default is exception.CantGuess:
        raise exception.CantGuess(what="dist",
                                  why="unknown branch '%s'" % branch)
    else:
        return default


def nvr(pkg=None, branch=None, default=exception.CantGuess):
    if not pkg:
        try:
            pkg = package()
        except exception.CantGuess:
            if default is exception.CantGuess:
                raise
            else:
                return default
    if not branch:
        try:
            branch = current_branch()
        except Exception:
            if default is exception.CantGuess:
                raise
            else:
                return default
    tag = branch
    if tag.startswith('el6-'):
        tag = "dist-6E-epel-testing-candidate"
    kojiout = run("koji", "latest-pkg",  "--quiet", tag, pkg,
                  fatal=False, print_output=True)
    if not kojiout.success:
        if default is exception.CantGuess:
            raise exception.CantGuess(what="nvr",
                                      why="koji query failed")
        else:
            return default
    m = re.match('^(\S+)\s+\S+\s+\S+$', kojiout)
    if not m:
        if default is exception.CantGuess:
            raise exception.CantGuess(what="nvr",
                                      why="can't parse koji output")
        else:
            return default
    return m.group(1)
