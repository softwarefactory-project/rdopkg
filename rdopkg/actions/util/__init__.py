from rdopkg.action import Action


ACTIONS = [
    Action('status', help="show status of previous action"),
    Action('conf', help="show rdopkg configuration"),
    Action('actions',
           help="list action functions and their availability"),
    Action('autocomplete',
           help="get TAB completion for rdopkg!"),
    Action('doctor',
           help="activate rdopkg psychoanalyst mode"),
]
