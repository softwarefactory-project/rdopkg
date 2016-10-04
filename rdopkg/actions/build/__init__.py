from rdopkg.action import Action, Arg


ACTIONS = [
    Action('coprbuild', atomic=True, help="build package in copr-jruzicka",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('copr_check'),
               Action('make_srpm', module='distgit'),
               Action('copr_upload'),
               Action('copr_build'),
           ],
           optional_args=[
               Arg('release', shortcut='-r',
                   help="OpenStack release (havana, icehouse, ...)"),
               Arg('dist', shortcut='-d',
                   help="target distribution (fedora-20, epel-7, ...)"),
               Arg('fuser', shortcut='-u',
                   help="Fedora user to upload srpm as to fedorapeople.org"),
           ]),
    Action('kojibuild', atomic=True, help="build package in koji",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('koji_build'),
           ]),
    Action('cbsbuild', atomic=True, help="build package in CBS",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('cbs_build'),
           ],
           optional_args=[
               Arg('scratch', action='store_true',
                   help='Perform a scratch build'),
           ]),
    Action('mockbuild', atomic=True, help="Run fedpkg/rhpkg mockbuild",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('fedpkg_mockbuild'),
           ]),
]
