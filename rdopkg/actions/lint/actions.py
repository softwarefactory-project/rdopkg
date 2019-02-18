"""
Check for common .spec problems
"""
from rdopkg.utils import specfile
from rdopkg.utils import lint as _lint


def lint(spec_fn=None, lint_checks=None, error_level='E'):
    if not spec_fn:
        spec_fn = specfile.spec_fn()
    if lint_checks:
        checks = lint_checks.split(',')
    else:
        checks = None
    hints = _lint.lint(spec_fn, checks=checks)
    _lint.lint_report(hints, error_level=error_level)
