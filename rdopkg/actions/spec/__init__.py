from rdopkg.action import Action, Arg


ACTIONS = [
    Action('get_tag',
           help="get TAG value from current .spec file",
           required_args=[
               Arg('tag', positional=True, metavar='TAG',
                   help='.spec file tag to show'),
           ],
           optional_args=[
               Arg('expand_macros', shortcut='-e', action='store_true',
                   help="expand macros in tag value (default: don't expand)"),
           ]),
    Action('set_tag',
           help="set TAG to VALUE in current .spec file",
           required_args=[
               Arg('tag', positional=True, metavar='TAG',
                   help='.spec file TAG to set'),
               Arg('value', positional=True, metavar='VALUE',
                   help='set to this VALUE'),
           ]),
    Action('get_macro',
           help="get RPM MACRO value from current .spec file",
           required_args=[
               Arg('macro', positional=True, metavar='MACRO',
                   help='RPM MACRO to show'),
           ],
           optional_args=[
               Arg('expand_macros', shortcut='-e', action='store_true',
                   help="expand macros in macro value "
                        "(default: don't expand)"),
           ]),
    Action('set_macro',
           help="set MACRO to VALUE in current .spec file",
           required_args=[
               Arg('macro', positional=True, metavar='MACRO',
                   help='RPM macro to set'),
               Arg('value', positional=True, metavar='VALUE',
                   help='set to this VALUE'),
           ]),
    Action('spec_eval',
           help="expand RPM EXPRESSION in context of current .spec file",
           required_args=[
               Arg('expression', positional=True, metavar='EXPRESSION',
                   help='RPM expression to expand')
           ]),
]
