from __future__ import print_function
from distroinfo.query import get_distrepos
import re
import pymod2pkg
import json

from rdopkg.actionmods import rdoinfo
from rdopkg.actionmods import query
from rdopkg import exception
from rdopkg.utils.git import git
from rdopkg.utils import log
from rdopkg.utils import specfile
from rdopkg import helpers


class DiffReq(object):

    def __init__(self, name, vers):
        self.name = name
        # ensure there is only one space between comp. operator and version
        vers = re.sub(r'([<>=!]+)', r'\1 ', vers.replace(" ", ""))
        self.vers = vers
        self.old_vers = vers

    def __str__(self, format=None):
        s = '%s %s' % (self.name, self.vers)
        if self.old_vers != self.vers:
            s += '  (was %s)' % (self.old_vers or 'not capped',)
        if not format:
            pass
        return s


class CheckReq(object):

    def __init__(self, name, desired_vers, vers, overridden=None,
                 ignored=False, autosync=None, autosync_error_msg=None):
        self.name = name
        self.desired_vers = self.extract_vers(desired_vers)
        self.vers = vers
        self.overridden = overridden
        self.ignored = ignored
        self.autosync = autosync
        self.autosync_error_msg = autosync_error_msg

    @staticmethod
    def extract_vers(vers):
        for rv in vers.split(','):
            m = re.match('(>|>=) (\\d.*)$', rv)
            if m:
                return rv
        return vers

    def met(self):
        if (self.desired_vers == self.vers) or (not self.desired_vers
                                                and not self.vers):
            return True
        else:
            return False

    def __str__(self, format='text'):
        s = self.name
        if self.desired_vers:
            s += ' ' + self.desired_vers
        if format == 'text':
            if self.vers:
                s += '  (%s in .spec)' % self.vers
            if self.overridden:
                s = ("{}, {t.bold}{t.warn}{} has been overridden in "
                     "requirements file{t.normal})".format(s[:-1],
                                                           self.overridden,
                                                           t=log.term))
            if self.autosync == "added":
                s = '{t.green}+ {}{t.normal}'.format(s, t=log.term)
            elif self.autosync == "edited":
                s = '{t.yellow}~ {}{t.normal}'.format(s, t=log.term)
            elif self.autosync == "removed":
                s = '{t.red}- {}{t.normal}'.format(s, t=log.term)
            elif self.autosync_error_msg:
                s = '{} {}'.format(s, self.autosync_error_msg)
        return s


def get_overridden_deps_of_pkg(overridden_deps, pkg_name):
    overridden_deps_of_pkg = dict()
    try:
        for cat in ['all', pkg_name]:
            if cat in overridden_deps['packages']:
                for dep in overridden_deps['packages'][cat]:
                    overridden_deps_of_pkg[dep['name']] = dep.get('version',
                                                                  '')
        return overridden_deps_of_pkg
    except Exception:
        log.error("The override file is not well formatted")
        exit(1)


def is_dependency_should_be_checked(python_version, environment_markers):
    env_markers = re.sub(r'[;\'"]', '', environment_markers.replace(" ", ""))
    env_markers = env_markers.split('or')
    should_be_checked = list()
    for marker in env_markers:
        if 'python_version' in marker:
            marker_version = marker.replace('python_version', '')
            mvr = match_version_rule(python_version, marker_version)
            if mvr == VER_OK:
                should_be_checked.append(True)
            else:
                should_be_checked.append(False)
    if len(should_be_checked) != 0 and True not in should_be_checked:
        return False
    return True


def parse_reqs_txt(txt, py_vers='3.6'):
    reqs = []
    if not txt:
        log.warn("The requirements.txt file is empty")
        return reqs
    lines = sorted(txt.split('\n'), key=lambda li: li.lower())
    for line in lines:
        # removing comments and spaces
        line = re.sub(r'\s*(?:#.*)$', '', line.replace(" ", ""))
        if not line:
            continue
        m = re.match(r'([\w\._-]+)([<>=!,.\d\w]*)(;.*)?$', line)
        if m:
            dep_name, dep_version, env_markers = m.groups()
            if env_markers is None:
                r = DiffReq(name=dep_name, vers=dep_version)
                reqs.append(r)
            else:
                if is_dependency_should_be_checked(py_vers, env_markers):
                    r = DiffReq(name=dep_name, vers=dep_version)
                    reqs.append(r)
        else:
            log.warn("Failed to parse requirement: %s" % line)
    return reqs


def get_reqs_from_ref(ref):
    try:
        o = git('show', '%s:requirements.txt' % ref, log_cmd=False)
        return parse_reqs_txt(o)
    except Exception:
        return ''


def get_upstream_first_ref_of_stable_releases_before(timestamp=None):
    upstream = list()
    for branch in git.remote_branches():
        if 'upstream/stable' in branch:
            commits = git.get_commits_of_branch(branch)
            try:
                if (commits[0]['timestamp'] < timestamp or timestamp is None):
                    upstream.append(commits[0]['hash'])
            except IndexError:
                pass
    return upstream


def get_reqs_present_in_upstream_before(timestamp, py_version='3.6'):
    reqs = list()
    for ref in get_upstream_first_ref_of_stable_releases_before(timestamp):
        reqs += get_reqs_from_ref(ref, py_version)
    return reqs


def get_pkgs_present_in_upstream_before(timestamp, py_version='3.6'):
    pkgs = list()
    reqs_txt = get_reqs_present_in_upstream_before(timestamp, py_version)
    map_reqs2pkgs(reqs_txt, 'epel')
    for _pkg in reqs_txt:
        if _pkg.name not in pkgs:
            pkgs.append(_pkg.name)
    return pkgs


def get_reqs_from_ref(ref, py_version='3.6'):
    try:
        o = git('show', '%s:requirements.txt' % ref, log_cmd=False)
    except Exception:
        o = ''
    return parse_reqs_txt(o, py_version)


def get_reqs_from_path(path, py_version='3.6'):
    o = open(path).read()
    return parse_reqs_txt(o, py_version)


def get_reqs_from_spec(as_objects=False, normalize_py23=False):
    spec = specfile.Spec()
    reqs = spec.get_requires_not_provided(versions_as_string=True,
                                          normalize_py23=normalize_py23)
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


def reqdiff_from_refs(ref1, ref2, py_version):
    r1 = get_reqs_from_ref(ref1, py_version)
    r2 = get_reqs_from_ref(ref2, py_version)
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


def reqcheck(desired_reqs, reqs, overridden_deps):
    met, any_version, wrong_version, missing, removed = [], [], [], [], []
    excess = reqs
    pkg_name = specfile.Spec().get_name()

    if overridden_deps:
        overridden_deps = get_overridden_deps_of_pkg(overridden_deps, pkg_name)
    else:
        overridden_deps = {}

    for dr in desired_reqs:
        overridden_vers, r, ignored = None, None, False
        for req in reqs:
            if req.name == dr.name:
                overridden_vers = None
                if req.name in overridden_deps:
                    overridden_vers = dr.vers
                    dr.vers = overridden_deps[req.name]
                    # we ignore the dependency if the version specified in
                    # the overridden file is empty.
                    if not dr.vers:
                        ignored = True
                r = CheckReq(dr.name, dr.vers, req.vers, overridden_vers,
                             ignored)

                try:
                    excess.remove(req)
                except Exception as ex:
                    pass
                break
        if not r:
            r = CheckReq(dr.name, dr.vers, None)

        try:
            if r.ignored:
                pass
            # If the module is not present as Require in the spec file
            elif r.vers is None:
                # If the module is ignored in an override file
                if r.name in overridden_deps and not overridden_deps[r.name]:
                    pass
                else:
                    missing.append(r)
            # If the module is not capped as Require in the spec file
            elif not r.vers:
                # If the module is capped in requirement file
                if r.desired_vers:
                    any_version.append(r)
                else:
                    met.append(r)
            else:
                if r.met():
                    met.append(r)
                else:
                    wrong_version.append(r)
            del r

        except Exception as ex:
            pass

    current_commit = git.current_commit()
    current_commit_timestamp = git.get_timestamp_by_ref(current_commit)
    pkgs_used_in_the_past = get_pkgs_present_in_upstream_before(
        current_commit_timestamp)
    for i, excess_pkg in enumerate(excess):
        if excess_pkg.name in pkgs_used_in_the_past:
            removed.append(CheckReq(excess_pkg.name, excess_pkg.vers, None))
            del excess[i]

    return met, any_version, wrong_version, missing, excess, removed


def print_reqcheck(met, any_version, wrong_version, missing, excess, removed,
                   format=None):
    cats = [
        ("{t.bold_green}{category}{t.normal}:", "met", met),
        ("{t.bold}{category}{t.normal}:", "any", any_version),
        ("{t.bold}{category}{t.normal}:", "excess", excess),
        ("{t.bold_yellow}{category}{t.normal}:", "mismatch",
         wrong_version),
        ("{t.bold_red}{category}{t.normal}:", "missing", missing),
        ("{t.bold_red}{category}{t.normal}:", "removed", removed),
    ]
    if format == 'json':
        output = {}
        for title, category, reqs in cats:
            if category not in output:
                output[category] = list()
            for req in reqs:
                output[category].append({'name': req.name, 'vers': req.vers})
        json_output = json.JSONEncoder().encode(output)
        print(json_output)
        return
    elif format == 'spec':
        # get alignment from .spec file
        spec = specfile.Spec()
        pre = 'Requires:' + (spec.get_tag_align_ws('Requires') or '        ')
    elif format == 'text':
        pre = '  '

    first = True
    for title, category, reqs in cats:
        if not reqs:
            continue
        if first:
            first = False
        else:
            print("")
        print(title.format(t=log.term, category=category.upper()))
        reqs = [x.__str__(format=format) for x in reqs]
        helpers.print_list(reqs, pre=pre)


def reqcheck_spec(py_version, ref=None, reqs_txt=None, override_pkgs=None):
    if (ref and reqs_txt) or (not ref and not reqs_txt):
        raise exception.InvalidUsage(
            why="reqcheck_spec needs either ref (git ref) or reqs_txt (path)")
    if ref:
        reqs_txt = get_reqs_from_ref(ref, py_version)
    else:
        reqs_txt = get_reqs_from_path(reqs_txt, py_version)
    map_reqs2pkgs(reqs_txt, 'epel')
    spec_reqs = get_reqs_from_spec(as_objects=True, normalize_py23=True)
    return reqcheck(reqs_txt, spec_reqs, override_pkgs)


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
    ri = rdoinfo.get_rdoinfo().get_info()
    distrepos = get_distrepos(ri, release=release, dist=dist)
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
