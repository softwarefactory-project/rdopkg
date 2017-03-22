# -*- encoding: utf-8 -*-

import argparse

import exception
from utils import log

ARGCOMPLETE_AVAILABLE = False
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    pass


def action2cmd(action):
    return action.replace('_', '-')


def optarg2cmdarg(arg):
    return "--%s" % action2cmd(arg)


def get_action_args(action, args):
    aargs = {}
    for rarg in action.required_args:
        aargs[rarg.name] = getattr(args, action2cmd(rarg.name))
    for oarg in action.optional_args:
        val = getattr(args, oarg.name)
        if val:
            aargs[oarg.name] = val
    return aargs


def get_parser(runner, version=None):
    parser = argparse.ArgumentParser(
        prog='rdopkg',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(help='available actions')
    parser.add_argument('-c', '--continue', action='store_true',
                        help='continue running current action')
    if version:
        parser.add_argument('--version', action='version', version=version)
    for action in runner.action_manager.actions:
        cmd = action2cmd(action.name)
        action_parser = subparsers.add_parser(
            cmd,
            help=action.help,
            description=action.description or action.help,
            formatter_class=argparse.RawDescriptionHelpFormatter)
        for oarg in action.optional_args:
            if oarg.positional:
                arg_names = [oarg.name]
            else:
                arg_names = oarg.cmdarg_names(optarg2cmdarg)
            action_parser.add_argument(*arg_names, **oarg.kwargs)
        for rarg in action.required_args:
            arg_names = rarg.cmdarg_names(action2cmd)
            action_parser.add_argument(*arg_names, **rarg.kwargs)
        action_parser.set_defaults(action=action)
    return parser


def run(action_runner, cargs, version=None):
    action_runner.load_state_safe()

    parser = get_parser(action_runner, version=version)
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)

    code = 1
    try:
        if not cargs:
            parser.print_help()
            return
        # argparse still can't do this with subparsers (reported 2009)
        elif '--abort' in cargs:
            action_runner.clear_state(verbose=True)
            return 1
        elif '--continue' in cargs or cargs == ('-c',):
            # state already loaded
            pass
        else:
            args = parser.parse_args(cargs)
            action = args.action
            action_args = get_action_args(action, args)
            action_runner.new_action(action, action_args)

        action_runner.engage()
        code = 0
    except (
            exception.ActionInProgress,
            exception.BranchNotFound,
            exception.BuildArchSanityCheckFailed,
            exception.CantGuess,
            exception.ConfigError,
            exception.CoprError,
            exception.CommandNotFound,
            exception.DebugAbort,
            exception.DuplicatePatchesBaseError,
            exception.FileNotFound,
            exception.IncompleteChangelog,
            exception.InvalidPackageFilter,
            exception.InvalidRDOPackage,
            exception.InvalidQuery,
            exception.InvalidUsage,
            exception.ManualResolutionNeeded,
            exception.NoPatchesChanged,
            exception.NotADirectory,
            exception.RequiredActionArgumentNotAvailable,
            exception.RequirementNotMet,
            exception.RpmModuleNotAvailable,
            exception.SpecFileNotFound,
            exception.ToolNotFound,
            exception.UserAbort,
            exception.UnverifiedPatch,
            KeyboardInterrupt,
    ) as ex:
        code = getattr(ex, 'exit_code', code)
        print("")
        print log.term.important(str(ex) or type(ex).__name__)
    except exception.NoActionInProgress as ex:
        print "%s See `rdopkg -h` for help." % ex
    except exception.CommandFailed as ex:
        # this was logged already
        pass
    except exception.InternalAction as ex:
        if ex.kwargs['action'] == 'status':
            action_runner.load_state_safe()
            action_runner.status()
            return 0
        elif ex.kwargs['action'] == 'actions':
            fails = action_runner.check_actions()
            return min(1, len(fails))
        raise
    return code
