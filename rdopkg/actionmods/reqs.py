import re


from rdopkg.utils.cmd import git
from rdopkg.utils import log
from rdopkg import helpers


class Req(object):
    def __init__(self, name, vers):
        self.name = name
        self.vers = vers
        self.old_vers = vers

    def __str__(self):
        s = '%s %s' % (self.name, self.vers)
        if self.old_vers != self.vers:
            s += '  (was %s)' % (self.old_vers or 'not capped',)
        return s


def parse_reqs_txt(txt):
    reqs = []
    lines = sorted(txt.split('\n'), key=lambda l: l.lower())
    for line in lines:
        if not line or re.match('\W', line):
            continue
        line = re.sub(r'\s*(?:#.*)$', '', line)
        m = re.match(r'([^<>=\s]+)(.*)$', line)
        if not m:
            log.warn("Failed to parse requirement: %s" % line)
            continue
        r = Req(name=m.group(1), vers=m.group(2))
        reqs.append(r)
    return reqs


def get_reqs_from_ref(ref):
    o = git('show', '%s:requirements.txt' % ref, log_cmd=False)
    return parse_reqs_txt(o)


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
