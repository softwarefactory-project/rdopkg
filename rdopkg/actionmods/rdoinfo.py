from __future__ import print_function
import distroinfo
import distroinfo.query
from distroinfo.info import DistroInfo

from rdopkg import exception, helpers
from rdopkg.utils import log
from rdopkg.conf import cfg


def print_releases(info):
    print("{t.bold}releases & repos:{t.normal}".format(t=log.term))
    for rls in info['releases']:
        s = "  {t.bold}{rls}{t.normal}".format(t=log.term, rls=rls['name'])
        if 'fedora' in rls:
            s += '   (Fedora %s)' % rls['fedora']
        print(s)
        for repo in rls['repos']:
            if 'special' in repo:
                print("    {t.bold}{name}{t.normal}: "
                      "{t.yellow}{special}{t.normal}".format(
                          t=log.term,
                          name=repo['name'],
                          special=repo['special']))
            else:
                print("    {t.bold}{name}{t.normal} built in"
                      " {t.bold}{bs}{t.normal} from"
                      " {t.bold}{branch}{t.normal} branch".format(
                          t=log.term,
                          name=repo['name'],
                          bs=repo.get('buildsys', '??'),
                          branch=repo['branch']))


def print_pkg_summary(info):
    pkgs = info['packages']
    n = len(pkgs)
    print("{t.bold}{n} packages defined:{t.normal}".format(
        t=log.term, n=n))
    confs = {}
    for pkg in pkgs:
        conf = pkg.get('conf')
        confs[conf] = confs.get(conf, 0) + 1

    for conf, n in confs.items():
        if not conf:
            continue
        print("  {t.bold}{n}{t.normal} using {t.bold}{conf}{t.normal} "
              "config".format(t=log.term, conf=conf, n=n))

    n = confs.get(None)
    if n:
        print("  {t.bold}{n}{t.normal} configured ad-hoc".format(
              t=log.term, n=n))


def print_summary(info):
    print_releases(info)
    print('')
    print_pkg_summary(info)


def print_pkgs(info, filters=None):
    pkgs = info['packages']
    if filters:
        pkgs = distroinfo.query.filter_pkgs(pkgs, rexen=filters)
    if not pkgs:
        print("No packages match your filter.")
        return
    print("{t.bold}{n} packages found:{t.normal}".format(t=log.term,
                                                         n=len(pkgs)))
    for pkg in pkgs:
        print("")
        print_pkg(pkg)


def print_pkg(pkg):
    dp = helpers.DictPrinter(
        header='name',
        first=['project', 'conf', 'upstream', 'patches', 'distgit', 'master',
               'distgit'],
        last=['maintainers'])
    dp(pkg)


def info_file(distro=None):
    """Return default distroinfo info file"""
    if not distro:
        distro = cfg['DISTRO']
    info_file_conf = distro.upper() + 'INFO_FILE'
    try:
        return cfg[info_file_conf]
    except KeyError:
        raise exception.InvalidUsage(
            why="Couldn't find config option %s for distro: %s"
                % (info_file_conf, distro))


def get_distroinfo(distro=None):
    """Get DistroInfo initialized from configuration"""
    if not distro:
        distro = cfg['DISTRO']
    _info_file = info_file(distro)
    # prefer git fetcher if available
    git_info_url_conf = distro.upper() + 'INFO_REPO'
    try:
        remote_git_info = cfg[git_info_url_conf]
        return DistroInfo(_info_file, remote_git_info=remote_git_info)
    except KeyError:
        pass
    # try raw remote fetcher
    remote_info_url_conf = distro.upper() + 'INFO_RAW_URL'
    try:
        remote_info = cfg[remote_info_url_conf]
        return DistroInfo(_info_file, remote_info=remote_info)
    except KeyError:
        raise exception.InvalidUsage(
            why="Couldn't find config option %s or %s for distro: %s"
                % (git_info_url_conf, remote_info_url_conf, distro))


def get_rdoinfo():
    """Compat function
    """
    return get_distroinfo(distro='rdo')


def get_default_inforepo(apply_tag=None, include_fns=None):
    raise DeprecationWarning("rdopkg >= 0.47.0 uses distroinfo, please use "
                             "`get_distroinfo` instead.")
