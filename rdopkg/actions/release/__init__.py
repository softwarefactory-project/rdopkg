from rdopkg.action import Action, Arg


ACTIONS = [
    Action('release', help="show information about RDO releases",
           optional_args=[
               Arg('release_specified', shortcut='-r',
                   help="fetch info about specified release"),
               Arg('local_info', shortcut='-l',
                   help="use local distroinfo repo found in specified path"),
               Arg('info_file', shortcut='-i',
                   help="use specified distroinfo info file")
           ])
]
