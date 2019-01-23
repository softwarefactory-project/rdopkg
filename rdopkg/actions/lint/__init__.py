from rdopkg.action import Action, Arg


ACTIONS = [
    Action('lint', help="check for common .spec problems",
           optional_args=[
               Arg('spec_fn', positional=True, nargs='?',
                   help="a .spec file to check"),
           ])
]
