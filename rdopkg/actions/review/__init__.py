from rdopkg.action import Action, Arg


ACTIONS = [
    Action('review_patch',
           help="send patch(es) for review",
           optional_args=[
               Arg('local_patches_branch', metavar='PATCHES_BRANCH',
                   positional=True, nargs='?',
                   help="local patches branch with changes to review"),
           ]),
    Action('review_spec', atomic=True,
           help="send distgit (.spec file) change for review",
           optional_args=[
               Arg('branch', metavar='DISTGIT_BRANCH',
                   positional=True, nargs='?',
                   help="local distgit branch with changes to review"),
           ],
           steps=[
               Action('get_package_env', module='distgit'),
               Action('review_spec'),
           ]),
]
