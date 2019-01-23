"""
Check for common .spec problems
"""
from rdopkg.utils import specfile
from rdopkg.utils import lint as _lint


def lint(spec_fn=None, lint_checks=None, lint_error_level='E'):
    if not spec_fn:
        spec_fn = specfile.spec_fn()
    hints = _lint.lint(spec_fn)
    _lint.lint_report(hints)
