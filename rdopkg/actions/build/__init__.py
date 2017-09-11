from rdopkg.action import Action, Arg


ACTIONS = [
    Action('kojibuild', help="build package in koji",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('koji_build'),
           ]),
    Action('cbsbuild', help="build package in CBS",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('cbs_build'),
           ],
           optional_args=[
               Arg('scratch', action='store_true',
                   help='Perform a scratch build'),
           ]),
    Action('mockbuild', help="Run fedpkg/rhpkg mockbuild",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('fedpkg_mockbuild'),
           ]),
]
