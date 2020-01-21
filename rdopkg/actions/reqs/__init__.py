from rdopkg.action import Action, Arg


ACTIONS = [
    Action('reqdiff', help="show diff of requirements.txt",
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
    Action('reqcheck',
           help="inspect requirements.txt vs .spec Requires",
           steps=[
               Action('get_package_env', module='distgit'),
               Action('reqcheck'),
               Action('reqcheck_autosync'),
               Action('reqcheck_print'),
           ],
           optional_args=[
               Arg('spec', shortcut='-s', action='store_true',
                   help="output .spec Requires: for easy pasting"
                        "Deprecated: use output instead."),
               Arg('strict', shortcut='-S', action='store_true',
                   help="Fail if not strictly matching"),
               Arg('version', shortcut='-R', metavar='VERSION',
                   help="query requirements.txt from VERSION git ref"),
               Arg('output', shortcut='-o', default='text',
                   help="output format to be used "
                        "(e.g: json, spec, text [default])"),
               Arg('python_version', shortcut='-p',
                   help="set the python version reference to evaluate if a "
                        "dependency should be checked or not (default 3.6)"),
               Arg('override', shortcut='-O', default=None,
                   help="overrides the behavior of reqcheck based on packages "
                        "that are in the file provided"),
               Arg('autosync', shortcut='-a', action='store_true',
                   help="synchronize spec and requirements files"),
           ]),
    Action('reqquery',
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
    Action('query',
           help="query RDO/dist repos for available package versions",
           optional_args=[
               Arg('filter', positional=True, metavar='RELEASE(/DIST)',
                   help="RDO release(/dist) to query (see `rdopkg info`)"),
               Arg('package', positional=True, metavar='PACKAGE',
                   help="package name to query about"),
               Arg('verbose', shortcut='-v', action='store_true',
                   help="print status during queries"),
           ]),
]
