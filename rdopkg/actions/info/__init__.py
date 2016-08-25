from rdopkg.action import Action, Arg


ACTIONS = [
    Action('info', atomic=True, help="show information about RDO packaging",
           optional_args=[
               Arg('pkgs', positional=True, nargs='*', metavar='ATTR:REGEX',
                   help="show info about packages with ATTR matching REGEX"),
               Arg('apply_tag', shortcut='-t',
                   help="apply overrides for selected tag"),
               Arg('force_fetch', shortcut='-f', action='store_true',
                   help="force fetch of info repo"),
               Arg('local_info', shortcut='-l',
                   help="use local rdoinfo repo found in specified path"),
           ]),
    Action('info_tags_diff', atomic=True,
           help="find which tags have changed between HEAD~..HEAD in rdoinfo",
           optional_args=[
               Arg('local_info', positional=True, metavar='RDOINFODIR',
                   help="use local rdoinfo repo found in RDOINFODIR"),
           ]),
    Action('findpkg', atomic=True,
           help="find and show single best matching package in rdoinfo",
           optional_args=[
               Arg('query', positional=True, metavar='PACKAGE/PROJECT/URL',
                   help="project name, package name or upstream URL"),
               Arg('strict', shortcut='-s', action='store_true',
                   help="only match whole pkg/proj/URL, no substring magics"),
               Arg('force_fetch', shortcut='-f', action='store_true',
                   help="force fetch of rdoinfo repo"),
               Arg('local_info', shortcut='-l',
                   help="use local rdoinfo repo found in specified path"),
           ]),
]
