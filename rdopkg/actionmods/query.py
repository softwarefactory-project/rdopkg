import re

from rdopkg.actionmods import rdoinfo
from rdopkg.utils import log
from rdopkg.utils.cmd import run
from rdopkg.utils.specfile import nvrcmp


def repoquery(repo_url, repo_name, package, verbose=False):
    repo_id = "rdopkg_%s" % re.sub('[^\w]', '_', repo_name)
    cmd = ["repoquery", "--nvr",
           "--repofrompath=%s,%s" % (repo_id, repo_url),
           "--repoid=%s" % repo_id, "-q", package]
    try:
        o = run(*cmd, log_cmd=verbose, log_fail=verbose)
    except Exception:
        return None
    lines = o.strip().split("\n")
    return lines[0] or None


def query_repos(distrepos, package, verbose=False):
    if not distrepos:
        return []
    versions = []
    for repo in distrepos:
        repo_name = repo['name']
        repo_url = repo['url']
        version = repoquery(repo_url, repo_name, package, verbose=verbose)
        if version:
            versions.append((repo_name, version))
        if verbose:
            log.info("%s: %s", repo_name, version or 'N/A')
    versions.sort(cmp=lambda x, y: nvrcmp(x[0], y[0]), reverse=True)
    return versions


def query_rdo(rlsdist, package, verbose=False):
    inforepo = rdoinfo.get_default_inforepo()
    inforepo.init()
    _release, _, _dist = rlsdist.partition('/')
    rds = inforepo.get_distrepos(_release, _dist)
    results = []
    for release, dist, distrepos in rds:
        r = query_repos(distrepos, package, verbose=verbose)
        results.append((release, dist, r))
    return results


def pretty_print_query_results(results):
    prls, pdist = None, None
    for rls, dist, vers in results:
        print(log.term.bold("%s/%s" % (rls, dist)))
        if not vers:
            print("    not available")
            continue
        first = True
        for rname, ver in vers:
            if first:
                fmt = "    {t.bold}{ver}{t.normal}  @  {rname}"
                first = False
            else:
                fmt = "    {ver}  @  {rname}"
            print(fmt.format(t=log.term, ver=ver, rname=rname))
