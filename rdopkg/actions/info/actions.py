import sys

from rdopkg.actionmods import rdoinfo
from rdopkg.utils import log


def info(pkgs=None, local_info=None, apply_tag=None, force_fetch=False):
    if local_info:
        inforepo = rdoinfo.RdoinfoRepo(
            local_repo_path=local_info,
            apply_tag=apply_tag)
    else:
        inforepo = rdoinfo.get_default_inforepo(apply_tag=apply_tag)
    inforepo.init(force_fetch=force_fetch)
    if pkgs:
        filters = {}
        for pf in pkgs:
            attr, sep, rex = pf.partition(':')
            if not sep:
                # filter by name by default
                attr = 'name'
                rex = pf
            filters[attr] = rex
        inforepo.print_pkgs(filters)
    else:
        inforepo.print_summary()
        print
        print("Supply regex filter(s) to list package details, e.g.:\n{t.cmd}"
              "    rdopkg info nova\n"
              "    rdopkg info conf:client maintainers:jruzicka\n"
              "    rdopkg info '.*'"
              "{t.normal}".format(t=log.term))


def info_tags_diff(local_info=None, apply_tag=None):
    if local_info:
        inforepo = rdoinfo.RdoinfoRepo(
            local_repo_path=local_info,
            apply_tag=apply_tag)
    else:
        inforepo = rdoinfo.get_default_inforepo(apply_tag=apply_tag)
    info1 = inforepo.get_info(gitrev='HEAD~')
    info2 = inforepo.get_info()
    tdiff = rdoinfo.tags_diff(info1, info2)
    if not tdiff:
        sys.stderr.write("No tag changes detected.\n")
    else:
        for pkg, changes in tdiff:
            print("%s %s" % (pkg, changes))
