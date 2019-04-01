from rdopkg.action import Action, Arg


ACTIONS = [
    Action('clone',
           help="custom clone action replacing internal one",
           required_args=[
               Arg('package', positional=True, metavar='PACKAGE',
                   help="custom package to clone"),
           ]),
]
