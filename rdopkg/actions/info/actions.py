from __future__ import print_function
from distroinfo.info import DistroInfo
import distroinfo.query
import sys

from rdopkg.actionmods import rdoinfo
from rdopkg import exception
from rdopkg import helpers
from rdopkg.utils import git
from rdopkg.utils import log


def info(pkgs=None, local_info=None, info_file=None,
         apply_tag=None, force_fetch=False):
    if not info_file:
        info_file = rdoinfo.info_file()
    if local_info:
        di = DistroInfo(info_file,
                        local_info=local_info)
    else:
        di = rdoinfo.get_distroinfo()
        if force_fetch:
            di.fetcher.cache_ttl = 0
    _info = di.get_info(apply_tag=apply_tag)
    if pkgs:
        filters = {}
        for pf in pkgs:
            attr, sep, rex = pf.partition(':')
            if not sep:
                # filter by name by default
                attr = 'name'
                rex = pf
            filters[attr] = rex
        rdoinfo.print_pkgs(_info, filters)
    else:
        rdoinfo.print_summary(_info)
        print('')
        print("Supply regex filter(s) to list package details, e.g.:\n{t.cmd}"
              "    rdopkg info nova\n"
              "    rdopkg info conf:client maintainers:jruzicka\n"
              "    rdopkg info '.*'"
              "{t.normal}".format(t=log.term))


def findpkg(query, strict=False, local_info=None, info_file=None,
            force_fetch=False):
    if not info_file:
        info_file = rdoinfo.info_file()
    if local_info:
        di = DistroInfo(info_file, local_info=local_info)
    else:
        di = rdoinfo.get_distroinfo()
        if force_fetch:
            di.fetcher.cache_ttl = 0
    _info = di.get_info()
    pkg = distroinfo.query.find_package(_info, query, strict=strict)
    if not pkg:
        raise exception.InvalidPackage(
            msg="No package found in distroinfo for query: %s" % query)
    rdoinfo.print_pkg(pkg)


def info_tags_diff(local_info, info_file=None, buildsys_tags=False):
    if not info_file:
        info_file = rdoinfo.info_file()
    di = DistroInfo(info_file, local_info=local_info)
    if buildsys_tags:
        tagsname = 'buildsys-tags'
    else:
        tagsname = 'tags'
    info2 = di.get_info()
    with helpers.cdir(di.fetcher.source):
        with git.git_revision('HEAD~'):
            info1 = di.get_info()
    tdiff = distroinfo.query.tags_diff(info1, info2, tagsname=tagsname)
    if not tdiff:
        sys.stderr.write("No tag changes detected.\n")
    else:
        for pkg, changes in tdiff:
            print("%s %s" % (pkg, changes))
