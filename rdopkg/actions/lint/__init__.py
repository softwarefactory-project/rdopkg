from rdopkg.action import Action, Arg


ACTIONS = [
    Action('lint', help="check for common .spec problems",
           optional_args=[
               Arg('spec_fn', positional=True, nargs='?',
                   help="a .spec file to check"),
               Arg('lint_checks', metavar='CHECKS',
                   help="comma-separated lists of checks to perform "
                        "(checks: sanity, rpmlint, all)"),
               Arg('error_level', metavar='E|W|-',
                   help="'E' to halt on errors (default), "
                        "'W' to halt on errors and warnings, "
                        "'-' to ignore errors (affects return value)")
           ])
]
