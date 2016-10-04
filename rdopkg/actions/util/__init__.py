from rdopkg.action import Action


ACTIONS = [
    Action('status', atomic=True, help="show status of previous action"),
    Action('conf', atomic=True, help="show rdopkg configuration"),
    Action('autocomplete', atomic=True,
           help="get TAB completion for rdopkg!"),
    Action('doctor', atomic=True,
           help="activate rdopkg psychoanalyst mode"),
]
