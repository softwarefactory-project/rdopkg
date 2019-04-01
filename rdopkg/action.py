from __future__ import print_function
import inspect
import pkgutil
import six

from rdopkg import exception
from rdopkg.utils import log

if six.PY2:
    inspect_getargspec = inspect.getargspec
else:
    inspect_getargspec = inspect.getfullargspec


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
    def __init__(self, name, steps=None, alias=None, continuable=False,
                 required_args=None, optional_args=None, const_args=None,
                 help=None, description=None, module=None, action_fun=None):
        if not const_args:
            const_args = []
        if not required_args:
            required_args = []
        if not optional_args:
            optional_args = []
        self.name = name
        self.module = module
        self.steps = steps
        self.alias = alias
        self.continuable = continuable
        self.action_fun = action_fun
        self.const_args = const_args
        self.required_args = required_args
        self.optional_args = optional_args
        self.help = help
        self.description = description

    def __repr__(self):
        return "ACTION: %s" % self.name


class ActionModule(object):
    def __init__(self, module, name=None):
        if not name:
            name = module.__name__
        self.name = name
        self.module = module
        self.actions = module.ACTIONS
        self._actionsmod = None

    @property
    def actionsmod(self):
        if not self._actionsmod:
            astr = self.module.__name__ + '.actions'
            apath = astr.split('.')
            topmod = __import__(astr, globals(), locals(), [])
            mod = topmod
            for submod in apath[1:]:
                mod = getattr(mod, submod)
            self._actionsmod = mod
        return self._actionsmod


class ActionManager(object):
    """This class manages action modules and contained actions."""
    def __init__(self):
        self.actions = []
        self.modules = []

    def _actions_dict(self):
        adict = {}
        for action in self.actions:
            adict[action.name] = action.module
        return adict

    def add_actions_module(self, module, name=None, override=True):
        def _assign_module(action, override=False):
            if override or not action.module:
                action.module = name
            if action.steps:
                for step in action.steps:
                    _assign_module(step)

        def _override_action(action):
            for i, _action in enumerate(self.actions):
                if _action.name == action.name:
                    self.actions[i] = action
                    break

        if not name:
            _, _, name = module.__name__.rpartition('.')
        adict = self._actions_dict()
        if not hasattr(module, 'ACTIONS'):
            raise exception.InvalidActionModule(
                module=module.__name__, why="missing ACTIONS description")
        for action in module.ACTIONS:
            if action.name in adict:
                # existing action
                if override:
                    _assign_module(action, override=True)
                    log.debug("overriding %s (module: %s -> %s)" %
                              (action, adict[action.name], name))
                    _override_action(action)
                else:
                    raise exception.DuplicateAction(
                        action=action.name, mod1=adict[action.name], mod2=name)
            else:
                # new action
                _assign_module(action, override=True)
                self.actions.append(action)
        self.modules.append(ActionModule(module, name))

    def add_actions_modules(self, package, override=True):
        added = []
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
            modpath = '%s.%s' % (package.__name__, modname)
            if not ispkg:
                continue
            try:
                mod = importer.find_module(modname).load_module(modname)
            except ImportError:
                log.warn("Failed to import module: %s" % modpath)
                continue
            if not hasattr(mod, 'ACTIONS'):
                continue
            self.add_actions_module(mod, name=modname, override=override)
            added += modname
        return added

    def fill_aliases(self):
        def _fill_alias(dst, src):
            for attr in ['help',
                         'description',
                         'optional_args',
                         'required_args']:
                src_val = getattr(src, attr)
                if not getattr(dst, attr) and src_val:
                    setattr(dst, attr, src_val)

        for a in self.actions:
            if not a.alias:
                continue
            for b in self.actions:
                if a.alias == b.name:
                    _fill_alias(a, b)

    def action_str(self, action):
        return ".".join(map(lambda x: x.name, action))

    def action_serialize(self, action):
        return list(map(lambda x: x.name, action))

    def action_deserialize(self, action_sr):
        action = []
        steps = self.actions
        for action_name in action_sr:
            found = False
            for step in steps:
                if six.text_type(step.name) == action_name:
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

    def _get_action_fun(self, action):
        fun = None
        for m in self.modules:
            if m.name != action.module:
                continue
            _fun = getattr(m.actionsmod, action.name, None)
            if _fun:
                fun = _fun
                break
        return fun

    def run_action(self, action, args=None):
        if not args:
            args = {}
        if action.continuable:
            log.info(log.term.bold("## %s" % action.name))
        for carg in action.const_args:
            args[carg] = action.const_args[carg]
        action_fun = action.action_fun
        if not action_fun:
            action_fun = self._get_action_fun(action)
            if not action_fun:
                raise exception.ActionFunctionNotAvailable(
                    action=action.name, module=action.module)
            action.action_fun = action_fun

        argspec = inspect_getargspec(action_fun)
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

    def print_actions(self):
        for action in self.actions:
            print(str(action))
