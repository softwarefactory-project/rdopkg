from rdopkg.action import Action, Arg


ACTIONS = [
    Action('info', help="show information about RDO packaging",
           optional_args=[
               Arg('pkgs', positional=True, nargs='*', metavar='ATTR:REGEX',
                   help="show info about packages with ATTR matching REGEX"),
               Arg('apply_tag', shortcut='-t',
                   help="apply overrides for selected tag"),
               Arg('force_fetch', shortcut='-f', action='store_true',
                   help="force fetch of info repo"),
               Arg('local_info', shortcut='-l',
                   help="use local distroinfo repo found in specified path"),
               Arg('info_file', shortcut='-i',
                   help="use specified distroinfo info file"),
           ]),
    Action('info_tags_diff',
           help=("find which tags have changed between HEAD~..HEAD"
                 " in distroinfo"),
           optional_args=[
               Arg('local_info', positional=True, metavar='INFO_REPO',
                   help="use local distroinfo repo found in INFO_REPO"),
               Arg('info_file', positional=True, metavar='INFO_FILE',
                   nargs='?',
                   help="use specified distroinfo INFO_FILE"),
               Arg('buildsys_tags', shortcut='-b', action='store_true',
                   help="process buildsys-tags instead of regular tags"),
           ]),
    Action('findpkg',
           help="find and show single best matching package in distroinfo",
           optional_args=[
               Arg('query', positional=True, metavar='PACKAGE/PROJECT/URL',
                   help="project name, package name or upstream URL"),
               Arg('strict', shortcut='-s', action='store_true',
                   help="only match whole pkg/proj/URL, no substring magics"),
               Arg('force_fetch', shortcut='-f', action='store_true',
                   help="force fetch of distroinfo repo"),
               Arg('local_info', shortcut='-l',
                   help="use local distroinfo repo found in specified path"),
               Arg('info_file', shortcut='-i',
                   help="use specified distroinfo info file"),
           ]),
]
