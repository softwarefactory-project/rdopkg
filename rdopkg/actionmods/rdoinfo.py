from __future__ import print_function
import collections
import imp
import re
import sys
import yaml

from rdopkg import exception
from rdopkg import helpers
from rdopkg import repoman
from rdopkg.utils import log
from rdopkg.utils.cmd import git
from rdopkg.conf import cfg


def filter_pkgs(pkgs, rexen):
    def _filter(pkg):
        for attr, rex in rexen.items():
            val = pkg.get(attr)
            if val is None:
                return False
            if isinstance(val, basestring):
                if not re.search(rex, val):
                    return False
            elif isinstance(val, collections.Iterable):
                # collection matches if any item of collection matches
                found = False
                for e in val:
                    if re.search(rex, e):
                        found = True
                        break
                if not found:
                    return False
            else:
                raise exception.InvalidPackageFilter(
                    why=("Can only filter strings but '%s' is %s"
                         % (attr, type(rex).__name__)))
        return True

    return filter(_filter, pkgs)


def tags_diff(info1, info2, tagsname='tags'):
    changedpkgs = []
    for pkg2 in info2["packages"]:
        if pkg2 not in info1["packages"]:
            changedpkgs.append(pkg2)
    diff = []
    for pkg2 in changedpkgs:
        foundpkg = False
        for pkg1 in info1["packages"]:
            if pkg1['name'] == pkg2['name']:
                foundpkg = True
                break
        updated_tags = []
        if foundpkg:
            for tag in pkg2.get(tagsname, {}):
                # use address of this function to differentiate
                # between missing tag and tag: None
                tag1 = pkg1.get(tagsname, {}).get(tag, tags_diff)
                if pkg2[tagsname][tag] != tag1:
                    updated_tags.append(tag)
        else:
            updated_tags = pkg2.get(tagsname).keys()
        if updated_tags:
            diff.append((pkg2['name'], updated_tags))
    return diff


def strip_project_url(url):
    """strip proto:// | openstack/ prefixes and .git | -distgit suffixes"""
    m = re.match(r'(?:[^:]+://)?(.*)', url)
    if m:
        url = m.group(1)
    if url.endswith('.git'):
        url, _, _ = url.rpartition('.')
    if url.endswith('-distgit'):
        url, _, _ = url.rpartition('-')
    if url.startswith('openstack/'):
        # openstack is always special :-p
        _, _, url = url.partition('/')
    return url


class RdoinfoRepo(repoman.RepoManager):
    repo_desc = 'info'

    def __init__(self, *args, **kwargs):
        self.info_file = kwargs.pop('info_file', 'rdo.yml')
        self.apply_tag = kwargs.pop('apply_tag', None)
        repoman.RepoManager.__init__(self, *args, **kwargs)
        self.rdoinfo = None
        self._info = None

    def ensure_rdoinfo(self):
        # when running get_info with gitrev, we are modifying rdoinfo module
        # while runing rdopkg. This seems to be problematic if we are using
        # the compiled .pyc so i'm forcing to load rdoinfo module from .py
        sys.dont_write_bytecode = True
        file, path, desc = imp.find_module('rdoinfo', [self.repo_path])
        self.rdoinfo = imp.load_module('rdoinfo', file, path, desc)
        sys.dont_write_bytecode = False

    def get_info(self, gitrev=None):
        with self.repo_dir():
            if gitrev:
                commit1 = git.current_commit()
                git('checkout', gitrev, log_cmd=False)
                self.ensure_rdoinfo()
                info = self.rdoinfo.parse_info_file(
                    self.info_file, apply_tag=self.apply_tag)
                git('checkout', commit1, log_cmd=False)
                self.ensure_rdoinfo()
            else:
                self.ensure_rdoinfo()
                info = self.rdoinfo.parse_info_file(
                    self.info_file, apply_tag=self.apply_tag)
        return info

    @property
    def info(self):
        if not self._info:
            self._info = self.get_info()
        return self._info

    def get_release(self, release):
        for rls in self.info['releases']:
            if rls.get('name') == release:
                return rls
        return None

    def get_package(self, name):
        for pkg in self.info['packages']:
            if pkg['name'] == name:
                return pkg
        return None

    def find_package(self, p, strict=False):
        # 1. strict package name matching (openstack-nova)
        pkg = self.get_package(p)
        if pkg:
            return pkg
        # 2. strict project/upstream matching (nova, git://../openstack/nova)
        ps = strip_project_url(p)
        for pkg in self.info['packages']:
            if 'project' in pkg and pkg['project'].lower() == ps:
                return pkg
            if 'upstream' in pkg:
                upstream = pkg['upstream']
                if strip_project_url(upstream) == ps:
                    return pkg
        if strict:
            return None
        # 3. best effort
        is_url = re.search(r'\W', ps)
        psl = ps.lower()
        if is_url:
            for pkg in self.info['packages']:
                if 'project' in pkg and pkg['project'].lower() in psl:
                    return pkg
        for pkg in self.info['packages']:
            if psl in pkg['name'].lower():
                return pkg
        return None

    def get_distrepos(self, release, dist=None):
        # release is required now, but this function can be extended to
        # return distrepos for multiple releases if needed
        rls = self.get_release(release)
        if not rls:
            why = 'release not defined in rdoinfo: %s' % release
            raise exception.InvalidQuery(why=why)
        found_dist = False
        distrepos = []
        for repo in rls['repos']:
            if dist and repo['name'] != dist:
                continue
            dr = repo.get('distrepos')
            if dr:
                distrepos.append((release, repo['name'], dr))
                if dist:
                    found_dist = True
                    break
        if dist and not found_dist:
            why = 'dist not defined in rdoinfo: %s/%s' % (release, dist)
            raise exception.InvalidQuery(why=why)
        if not distrepos:
            why = 'No distrepos information in rdoinfo for %s' % release
            raise exception.InvalidQuery(why=why)

        return distrepos

    def print_releases(self):
        print("{t.bold}RDO releases & repos:{t.normal}".format(t=log.term))
        for rls in self.info['releases']:
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

    def print_pkg_summary(self):
        pkgs = self.info['packages']
        n = len(pkgs)
        print("{t.bold}{n} RDO packages defined:{t.normal}".format(
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

    def print_summary(self):
        self.print_releases()
        print('')
        self.print_pkg_summary()

    def print_pkgs(self, filters=None):
        pkgs = self.info['packages']
        if filters:
            pkgs = filter_pkgs(pkgs, rexen=filters)
        if not pkgs:
            print("No packages match your filter.")
            return
        print("{t.bold}{n} packages found:{t.normal}".format(t=log.term,
                                                             n=len(pkgs)))
        for pkg in pkgs:
            print("")
            print_pkg(pkg)


def get_default_inforepo(apply_tag=None):
    return RdoinfoRepo(
        cfg['HOME_DIR'],
        cfg['RDOINFO_REPO'],
        apply_tag=apply_tag)


def print_pkg(pkg):
    dp = helpers.DictPrinter(
        header='name',
        first=['project', 'conf', 'upstream', 'patches', 'distgit', 'master',
               'distgit'],
        last=['maintainers'])
    dp(pkg)
