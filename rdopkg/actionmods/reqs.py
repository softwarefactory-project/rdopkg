import re


from rdopkg.actionmods import pymod2pkg
from rdopkg import exception
from rdopkg.utils.cmd import git
from rdopkg.utils import log
from rdopkg.utils import specfile
from rdopkg import helpers


class DiffReq(object):
    def __init__(self, name, vers):
        self.name = name
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


def get_reqs_from_spec():
    spec = specfile.Spec()
    return spec.get_requires(versions_as_string=True)


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


def map_reqs2pkgs(reqs, dist):
    for r in reqs:
        r.name = pymod2pkg.module2package(r.name, dist)
    return reqs


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
        ("\n{t.bold_green}MET{t.normal}:", met),
        ("\n{t.bold}VERSION NOT ENFORCED{t.normal}:", any_version),
        ("\n{t.bold_yellow}VERSION MISMATCH{t.normal}:", wrong_version),
        ("\n{t.bold_red}MISSING{t.normal}:", missing),
        ]
    for title, reqs in cats:
        if not reqs:
            continue
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
