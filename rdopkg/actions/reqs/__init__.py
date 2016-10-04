from rdopkg.action import Action, Arg


ACTIONS = [
    Action('reqdiff', atomic=True, help="show diff of requirements.txt",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('get_diff_range', module='distgit'),
               Action('reqdiff'),
           ],
           optional_args=[
               Arg('diff_range', positional=True, nargs='*', metavar='GIT_REF',
                   help="no args: diff between current and upstream; "
                        "1 arg: diff between current and supplied git ref; "
                        "2 args: diff between 1st and 2nd supplied git refs"),
           ],
           ),
    Action('reqcheck', atomic=True,
           help="inspect requirements.txt vs .spec Requires",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('reqcheck'),
           ]),
    Action('reqquery', atomic=True,
           help="query RDO repos for versions defined in requirements.txt",
           required_args=[
               Arg('filter', positional=True, metavar='RELEASE(/DIST)',
                   nargs='?',
                   help="RDO release(/dist) to query (see `rdopkg info`)"),
           ],
           optional_args=[
               Arg('reqs_file', shortcut='-r', metavar='FILE',
                   help="query supplied requirements.txt FILE"),
               Arg('reqs_ref', shortcut='-R', metavar='VERSION',
                   help="query requirements.txt from VERSION git ref"),
               Arg('spec', shortcut='-s', action='store_true',
                   help="query .spec file in current directory"),
               Arg('load', shortcut='-l', action='store_true',
                   help="load query results from requirements.yml "
                        "(created with -d)"),
               Arg('load_file', shortcut='-L', metavar='FILE',
                   help="load query results from FILE (created with -D)"),
               Arg('dump', shortcut='-d', action='store_true',
                   help="dump query results to requirements.yml "
                        "(view with -l)"),
               Arg('dump_file', shortcut='-D', metavar='FILE',
                   help="dump query results to FILE (view with -L)"),
               Arg('verbose', shortcut='-v', action='store_true',
                   help="print status during queries"),
           ]),
    Action('query', atomic=True, help="query RDO and distribution repos for "
                                      "available package versions",
           optional_args=[
               Arg('filter', positional=True, metavar='RELEASE(/DIST)',
                   help="RDO release(/dist) to query (see `rdopkg info`)"),
               Arg('package', positional=True, metavar='PACKAGE',
                   help="package name to query about"),
               Arg('verbose', shortcut='-v', action='store_true',
                   help="print status during queries"),
           ]),
]
