import re
import pymod2pkg


from rdopkg.actionmods import rdoinfo
from rdopkg.actionmods import query
from rdopkg import exception
from rdopkg.utils.cmd import git
from rdopkg.utils import log
from rdopkg.utils import specfile
from rdopkg import helpers


class DiffReq(object):

    def __init__(self, name, vers):
        self.name = name
        # ensure that comp. operators are surrounded with spaces
        vers = re.sub(r'([<>=!]+)', r'\1 ', vers)
        self.vers = vers
        self.old_vers = vers

    def __str__(self):
        s = '%s %s' % (self.name, self.vers)
        if self.old_vers != self.vers:
            s += '  (was %s)' % (self.old_vers or 'not capped',)
        return s


class CheckReq(object):

    def __init__(self, name, desired_vers, vers):
        self.name = name
        self.desired_vers = desired_vers
        self.vers = vers

    def met(self):
        if self.vers is None:
            return False
        # TODO: smarter version rage comparison
        if self.desired_vers:
            if self.desired_vers == self.vers:
                return True
            else:
                return False
        return True

    def __str__(self):
        s = self.name
        if self.desired_vers:
            s += ' ' + self.desired_vers
        if self.vers:
            s += '  (%s in .spec)' % self.vers
        return s


def parse_reqs_txt(txt):
    reqs = []
    lines = sorted(txt.split('\n'), key=lambda l: l.lower())
    for line in lines:
        if not line or re.match('\W', line):
            continue
        line = re.sub(r'\s*(?:#.*)$', '', line)
        m = re.match(r'([^<>=!\s]+)\s*(.*)$', line)
        if not m:
            log.warn("Failed to parse requirement: %s" % line)
            continue
        r = DiffReq(name=m.group(1), vers=m.group(2))
        reqs.append(r)
    return reqs


def get_reqs_from_ref(ref):
    o = git('show', '%s:requirements.txt' % ref, log_cmd=False)
    return parse_reqs_txt(o)


def get_reqs_from_path(path):
    o = open(path).read()
    return parse_reqs_txt(o)


def get_reqs_from_spec(as_objects=False):
    spec = specfile.Spec()
    reqs = spec.get_requires(versions_as_string=True)
    if as_objects:
        creqs = []
        for name in sorted(reqs):
            req = DiffReq(name, reqs[name])
            creqs.append(req)
        return creqs
    return reqs


def map_reqs2pkgs(reqs, dist):
    for r in reqs:
        r.name = pymod2pkg.module2package(r.name, dist)
    return reqs


def reqdiff(reqs1, reqs2):
    added, changed = [], []
    removed = list(reqs1)

    for r2 in reqs2:
        for r1 in reqs1:
            if r1.name == r2.name:
                if r1.vers != r2.vers:
                    r2.old_vers = r1.vers
                    changed.append(r2)
                try:
                    removed.remove(r1)
                except Exception as ex:
                    pass
                break
        else:
            added.append(r2)

    return added, changed, removed


def reqdiff_from_refs(ref1, ref2):
    r1 = get_reqs_from_ref(ref1)
    r2 = get_reqs_from_ref(ref2)
    return reqdiff(r1, r2)


def print_reqdiff(added, changed, removed):
    if added:
        print("\n{t.bold}ADDED{t.normal}:".format(t=log.term))
        helpers.print_list(added, pre='  ')
    if changed:
        print("\n{t.bold}CHANGED{t.normal}:".format(t=log.term))
        helpers.print_list(changed, pre='  ')
    if removed:
        print("\n{t.bold}REMOVED{t.normal}:".format(t=log.term))
        helpers.print_list(removed, pre='  ')
    if not (added or changed or removed):
        print("\nno requirements changed")
    print("")


def reqcheck(desired_reqs, reqs):
    met, any_version, wrong_version, missing = [], [], [], []
    for dr in desired_reqs:
        vers = reqs.get(dr.name)
        r = CheckReq(dr.name, dr.vers, vers)
        if r.vers is None:
            missing.append(r)
        elif r.vers is '':
            if r.desired_vers:
                any_version.append(r)
            else:
                met.append(r)
        else:
            if r.met():
                met.append(r)
            else:
                wrong_version.append(r)

    return met, any_version, wrong_version, missing


def print_reqcheck(met, any_version, wrong_version, missing):
    cats = [
        ("{t.bold_green}MET{t.normal}:", met),
        ("{t.bold}VERSION NOT ENFORCED{t.normal}:", any_version),
        ("{t.bold_yellow}VERSION MISMATCH{t.normal}:", wrong_version),
        ("{t.bold_red}MISSING{t.normal}:", missing),
    ]
    first = True
    for title, reqs in cats:
        if not reqs:
            continue
        if first:
            first = False
        else:
            print("")
        print(title.format(t=log.term))
        helpers.print_list(reqs, pre='  ')


def reqcheck_spec(ref=None, reqs_txt=None):
    if (ref and reqs_txt) or (not ref and not reqs_txt):
        raise exception.InvalidUsage(
            why="reqcheck_spec needs either ref (git ref) or reqs_txt (path)")
    if ref:
        reqs_txt = get_reqs_from_ref(ref)
    else:
        reqs_txt = get_reqs_from_path(reqs_txt)
    map_reqs2pkgs(reqs_txt, 'epel')
    spec_reqs = get_reqs_from_spec()
    return reqcheck(reqs_txt, spec_reqs)


VER_OK, VER_FAIL, VER_WTF = range(3)
VERCMP_TABLE = {
    '<': [-1],
    '<=': [-1, 0],
    '>': [1],
    '>=': [1, 0],
    '==': [0],
    '=': [0],
    '!=': [-1, 1],
}
VERCMP_COLORS = {
    VER_OK: 'green',
    VER_FAIL: 'red',
    VER_WTF: 'yellow'
}


def match_version_rule(ver, rver):
    m = re.match('(<|<=|>|>=|==|=|!=)(\d.*)$', rver)
    if not m:
        return VER_WTF
    op, rv = m.groups()
    goal = VERCMP_TABLE.get(op, [])
    c = specfile.vcmp(ver, rv)
    if c in goal:
        return VER_OK
    return VER_FAIL


def match_required_vers(ver, rvers):
    if not rvers:
        if ver:
            return [('any version', VER_OK)]
        else:
            return [('any version', VER_FAIL)]
    matches = []
    for rv in rvers.split(','):
        matches.append((rv, match_version_rule(ver, rv)))
    return matches


def color_matched_required_vers(matches):
    vers = []
    for ver, m in matches:
        s = '{t.%s}{v}{t.normal}' % VERCMP_COLORS[m]
        vers.append(s.format(t=log.term, v=ver))
    return ','.join(vers)


def reqquery(reqs, release, dist=None, module2pkg=True, verbose=False):
    info = rdoinfo.get_default_inforepo()
    distrepos = info.get_distrepos(release=release, dist=dist)
    r = []
    for rls, dist, repos in distrepos:
        packages = []
        for req in reqs:
            if module2pkg:
                pkg_name = pymod2pkg.module2package(req.name, dist)
            else:
                pkg_name = req.name
            vers = query.query_repos(repos, pkg_name, verbose=verbose)
            repo, nvr, v = None, None, None
            if vers:
                repo, nvr = vers[0]
                v = specfile.nvr2version(nvr)
            pkg = {
                'package': pkg_name,
                'version_required': req.vers or None,
                'version_available': v,
                'nvr_available': nvr,
                'repo_available': repo,
            }
            if module2pkg:
                pkg['module'] = req.name
            packages.append(pkg)
        vers = {
            'release': rls,
            'dist': dist,
            'packages': packages
        }
        r.append(vers)
    return r


def print_reqquery(q):
    first = True
    for ver in q:
        if first:
            first = False
        else:
            print('')
        fmt = "\n{t.bold}{rls}{t.normal}/{t.bold}{dist}{t.normal}"
        print(fmt.format(t=log.term, rls=ver['release'], dist=ver['dist']))
        for pkg in ver['packages']:
            module = pkg.get('module') or pkg['package']
            mvers = match_required_vers(pkg['version_available'],
                                        pkg['version_required'])
            cvers = color_matched_required_vers(mvers)
            nvr = pkg['nvr_available']
            if nvr and pkg['version_available']:
                nvr = re.sub(re.escape(pkg['version_available']),
                             '{t.bold}%s{t.normal}' % pkg['version_available'],
                             nvr)
                nvr = nvr.format(t=log.term)
            print("  {t.bold}{m}{t.normal}".format(t=log.term, m=module))
            if nvr:
                print("    nvr:   %s" % nvr)
            else:
                fmt = "    nvr:   {pkg} {t.red}not available{t.normal}"
                print(fmt.format(t=log.term, pkg=pkg['package']))
            print("    need:  %s" % cvers)
            met = '{t.green}OK{t.normal}'
            for _, m in mvers:
                if m != VER_OK:
                    met = '{t.red}not met{t.normal}'
                    break
            print(("    state: " + met).format(t=log.term))
