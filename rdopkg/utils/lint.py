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

    def pretty_str(self):
        fmt = "{loc}: {t.%s}{lvl}{t.normal}: {t.bold}{msg1}{t.normal} {msg2}"
        if self.level == 'W':
            color = 'yellow'
        else:
            color = 'red'
        fmt = fmt % color
        msg1, _, msg2 = self.msg.partition(' ')
        return fmt.format(
            loc=self.location,
            lvl=self.level,
            msg1=msg1,
            msg2=msg2,
            t=log.term
        )


RE_RPMLINT_HINT = r'(.*):\s+([EW]):\s+(.+)$'
RE_RPMLINT_SUMMARY = (r'\d+ packages and \d+ specfiles checked; '
                      r'\d+ errors?, \d+ warnings?.')


def rpmlint_check(*args):
    # run rpmlint and return linting hints it found
    hints = []
    cmd = ['rpmlint']
    if args:
        cmd += args
    try:
        out = run(*cmd, fatal=False, log_fail=False)
    except exception.CommandNotFound:
        raise exception.CommandNotFound(
            msg="Unable to run rpmlint checks because rpmlint is missing.")
    for line in out.splitlines():
        m = re.match(RE_RPMLINT_HINT, line)
        if m:
            hints.append(LintHint(location=m.group(1),
                                  level=m.group(2),
                                  msg=m.group(3)))
            continue
        m = re.match(RE_RPMLINT_SUMMARY, line)
        if m:
            # ignore final rpmlint summary
            continue
        hints.append(LintHint(location='rpmlint', level='W', msg=(
            'Failed to parse rpmlint output: %s' % line)))
    return hints


def sanity_check_buildarch(txt):
    # make sure BuildArch is AFTER SourceX and PatchX lines,
    # otherwise %{patches} macro is empty which causes trouble
    bm = re.search(r'^BuildArch:', txt, flags=re.M)
    if not bm:
        return True
    bi = bm.start()
    sm = re.search(r'^Source\d+:', txt, flags=re.M)
    if sm:
        si = sm.start()
        if bi < si:
            return False
    pm = re.search(r'^Patch\d+:', txt, flags=re.M)
    if pm:
        pi = pm.start()
        if bi < pi:
            return False
    return True


def sanity_check_patches_base(txt):
    # duplicate patches_base might lead to unexpected behavior
    bases = re.findall(r'^#\s*patches_base', txt, flags=re.M)
    if len(bases) > 1:
        return False
    return True


def sanity_check(spec_fn):
    # perform rdopkg sanity checks for common problems
    hints = []
    try:
        txt = open(spec_fn, 'r').read()
    except Exception as e:
        hints.append(LintHint(
            spec_fn, 'E', str(e)))
        return hints
    if not sanity_check_buildarch(txt):
        hints.append(LintHint(spec_fn, 'E', (
            "buildarch-before-sources: Due to mysterious"
            "ways of rpm, BuildArch needs to be placed "
            "AFTER SourceX and PatchX lines in .spec file, "
            "otherwise %{patches} macro will be empty "
            "and both %autosetup and `git am %{patches}` will fail. "
            "Please move BuildArch AFTER SourceX and PatchX lines.")))
    if not sanity_check_patches_base(txt):
        hints.append(LintHint(spec_fn, 'E', (
            "duplicate-patches-base: Please make sure to only have one "
            "# patches_base= entry in .spec file to avoid problems.")))
    return hints


LINT_CHECKS = {
    'sanity': sanity_check,
    'rpmlint': rpmlint_check,
}


def lint(spec_fn, checks=None):
    if not checks or checks == 'all':
        # use all checks by default
        checks = LINT_CHECKS.keys()
    hints = []
    for ch in checks:
        try:
            check = LINT_CHECKS[ch]
        except KeyError:
            raise exception.InvalidLintCheck(check=ch)
        hints += check(spec_fn)
    return hints


def lint_report(hints, error_level=None):
    # print a linting report based on passed hints
    # optionally raise error depending on error_level:
    #   * 'E': raise when errors found
    #   * 'W': raise when errors or warnings are found
    #   * other: don't raise error, only print report
    hint_dict = defaultdict(list)
    for hint in hints:
        hint_dict[hint.level].append(hint)

    errors = hint_dict.get('E', [])
    n_errors = len(errors)
    if errors:
        print("\n{t.red}{n} ERRORS found:{t.normal}".format(
            n=n_errors, t=log.term))
        for e in errors:
            print(e.pretty_str())

    warns = hint_dict.get('W', [])
    n_warns = len(warns)
    if warns:
        print("\n{t.yellow}{n} WARNINGS found:{t.normal}".format(
            n=n_warns, t=log.term))
        for e in warns:
            print(e.pretty_str())

    if n_errors == 0 and n_warns == 0:
        print("\n{t.green}no linting errors found \\o/{t.normal}".format(
            t=log.term))
        return

    critical_error = False
    if error_level == 'E' and n_errors > 0:
        critical_error = True
    if error_level == 'W' and (n_errors > 0 or n_warns > 0):
        critical_error = True
    if critical_error:
        raise exception.LintProblemsFound(
            "Linting problems detected: %d errors, %d warnings" % (
                n_errors, n_warns))
