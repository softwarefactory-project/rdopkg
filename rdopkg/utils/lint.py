"""
Check for common .spec problems
"""

from collections import defaultdict
import re

from rdopkg import exception
from rdopkg.utils import log
from rdopkg.utils.cmd import run
from rdopkg import helpers


class LintHint(object):
    def __init__(self, location, level, msg):
        self.location = location
        self.level = level
        self.msg = msg

    def __repr__(self):
        return ('%s: %s: %s' %
                (self.location, self.level, self.msg))


RE_RPMLINT_HINT = r'(.*):\s+([EW]):\s+(.+)$'


def rpmlint_check(*args):
    hints = []
    cmd = ['rpmlint']
    if args:
        cmd += args
    out = run(*cmd, fatal=False, log_fail=False)
    for line in out.splitlines():
        m = re.match(RE_RPMLINT_HINT, line)
        if m:
            hints.append(LintHint(location=m.group(1),
                                  level=m.group(2),
                                  msg=m.group(3)))
            continue
        hints.append(LintHint(location='rpmlint', level='W', msg=(
            'Failed to parse rpmlint output: %s' % line)))
    return hints


def sanity_check_buildarch(txt):
    # make sure BuildArch is AFTER SourceX and PatchX lines,
    # otherwise %{patches} macro is empty which causes trouble
    bm = re.search('^BuildArch:', txt, flags=re.M)
    if not bm:
        return True
    bi = bm.start()
    sm = re.search('^Source\d+:', txt, flags=re.M)
    if sm:
        si = sm.start()
        if bi < si:
            return False
    pm = re.search('^Patch\d+:', txt, flags=re.M)
    if pm:
        pi = pm.start()
        if bi < pi:
            return False


def sanity_check_patches_base(txt):
    # duplicate patches_base might lead to unexpected behavior
    bases = re.findall('^#\s*patches_base', txt, flags=re.M)
    if len(bases) > 1:
        return False
    return True


def sanity_check(spec_fn):
    hints = []
    try:
        txt = open(spec_fn, 'r').read()
    except Exception as e:
        hints.append(LintHint(
            spec_fn, 'E', str(e)))
        return hints
    if not sanity_check_buildarch(txt):
        hints.append(LintHint(spec_fn, 'E', (
            "Due to mysterious ways of rpm, BuildArch needs to be placed "
            "AFTER SourceX and PatchX lines in .spec file, "
            "otherwise %%{patches} macro will be empty "
            "and both %%autosetup and `git am %%{patches}` will fail. "
            "Please move BuildArch AFTER SourceX and PatchX lines.")))
    if not sanity_check_patches_base(txt):
        hints.append(LintHint(spec_fn, 'E', (
            "Please make sure to only have one "
            "# patches_base= entry in .spec file")))
    return hints


LINT_CHECKS = {
    'sanity': sanity_check,
    'rpmlint': rpmlint_check,
}


def lint(spec_fn, checks=None):
    if not checks or checks == 'all':
        checks = LINT_CHECKS.keys()
    hints = []
    for ch in checks:
        try:
            check = LINT_CHECKS[ch]
        except KeyError:
            raise exception.InvalidLintCheck(check=ch)
        hints += check(spec_fn)
    return hints


def lint_report(hints, error_level='E'):
    hint_dict = defaultdict(list)
    for hint in hints:
        hint_dict[hint.level].append(hint)

    errors = hint_dict.get('E', [])
    n_errors = len(errors)
    if errors:
        print("%d ERRORS found:" % n_errors)
        for e in errors:
            print(e)
        print('')

    warns = hint_dict.get('W', [])
    n_warns = len(warns)
    if warns:
        print("%d WARNINGS found:" % n_warns)
        for e in warns:
            print(e)
        print('')

    if n_errors == 0 and n_warns == 0:
        print("no linting errors found \o/")

    # TODO: raise on errors/warns depending on error_level

