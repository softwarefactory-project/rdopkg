import inspect

import exception
from utils import log


class Arg(object):

    def __init__(self, name, **kwargs):
        self.name = name
        self.shortcut = kwargs.pop('shortcut', None)
        self.positional = kwargs.pop('positional', False)
        self.kwargs = kwargs

    def cmdarg_names(self, name2argfun):
        names = []
        if self.shortcut:
            names.append(self.shortcut)
        names.append(name2argfun(self.name))
        return names


class Action(object):

    def __init__(self, name, steps=None, atomic=False, action_fun=None,
                 required_args=None, optional_args=None, const_args=None,
                 help=None):
        if not const_args:
            const_args = []
        if not required_args:
            required_args = []
        if not optional_args:
            optional_args = []
        self.name = name
        self.steps = steps
        self.atomic = atomic
        self.action_fun = action_fun
        self.const_args = const_args
        self.required_args = required_args
        self.optional_args = optional_args
        self.help = help


class ActionModule(object):

    def __init__(self, module, name=None):
        if not name:
            name = module.__name__
        self.name = name
        self.module = module
        self.actions = module.ACTIONS


class ActionManager(object):
    """
    This class manages all actions available.

    Action namespaces might be added, but I'm not convinced it'd be worth it,
    so there is no such thing now.
    """

    def __init__(self):
        self.actions = []
        self.modules = []

    def add_actions_module(self, module, name=None):
        # TODO: once this is used, check for duplicate actions and other errors
        self.actions += module.ACTIONS
        self.modules.append(ActionModule(module, name))

    def action_str(self, action):
        return ".".join(map(lambda x: x.name, action))

    def action_serialize(self, action):
        return map(lambda x: x.name, action)

    def action_deserialize(self, action_sr):
        action = []
        steps = self.actions
        for action_name in action_sr:
            found = False
            for step in steps:
                if unicode(step.name) == action_name:
                    action.append(step)
                    steps = step.steps or []
                    found = True
                    break
            if not found:
                astr = self.action_str(action + [Action(action_name)])
                raise exception.InvalidAction(action=astr)
        return action

    def ensure_leaf_action(self, action, on_change_callback=None):
        step = action[-1]
        if step.steps:
            while step.steps:
                next_step = step.steps[0]
                action.append(next_step)
                step = next_step
            if on_change_callback:
                on_change_callback()
        return action

    def next_action(self, action):
        while action:
            last = action[-1]
            if len(action) <= 1:
                return None
            parent = action[-2]
            found = False
            for step in parent.steps:
                if step == last:
                    found = True
                elif found:
                    action = action[:-1] + [step]
                    return self.ensure_leaf_action(action)
            action = action[:-1]
        return None

    def _get_action_fun(self, name):
        fun = None
        module_name = None
        for m in self.modules:
            _fun = getattr(m.module, name, None)
            if _fun:
                fun = _fun
                module_name = m.name
                break
        return fun, module_name

    def run_action(self, action, args=None):
        if not args:
            args = {}
        if not action.atomic:
            log.info(log.term.bold("## %s" % action.name))
        for carg in action.const_args:
            args[carg] = action.const_args[carg]
        action_fun = action.action_fun
        if not action_fun:
            action_fun, action_module = self._get_action_fun(action.name)
            if not action_fun:
                raise exception.ActionFunctionNotAvailable(action=action.name)
        argspec = inspect.getargspec(action_fun)
        fun_args = []
        if argspec.defaults:
            n_defaults = len(argspec.defaults)
        else:
            n_defaults = 0
        n_required = len(argspec.args) - n_defaults
        for i, arg in enumerate(argspec.args):
            if arg in args:
                fun_args.append(args[arg])
            else:
                if i < n_required:
                    raise exception.RequiredActionArgumentNotAvailable(
                        action=action.name, arg=arg)
                else:
                    fun_args.append(argspec.defaults[i - n_required])
        return action_fun(*fun_args)
