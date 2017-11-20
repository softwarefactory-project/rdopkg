# -*- encoding: utf-8 -*-
from __future__ import print_function
import json
import os
from six.moves import input

from rdopkg import action as _action
from rdopkg import actions
from rdopkg import const
from rdopkg import exception
from rdopkg import helpers
from rdopkg.utils import log


def default_action_manager():
    action_manager = _action.ActionManager()
    action_manager.add_actions_module(actions, 'base')
    return action_manager


class ActionRunner(object):

    def __init__(self, action_manager=None, state_file_path=None):
        if not action_manager:
            action_manager = default_action_manager()
        self.action_manager = action_manager
        self.action = []
        self.args = {}
        self.state_file_path = state_file_path or const.STATE_FILE_FN

    def save_state(self):
        if not (self.action and self.action[0].continuable):
            return
        data = {
            'action': self.action_manager.action_serialize(self.action),
            'args': self.args
        }
        sf = open(self.state_file_path, 'wt')
        json.dump(data, sf)
        sf.close()

    def get_state(self):
        if not os.path.isfile(self.state_file_path):
            return None
        with open(self.state_file_path, 'rt') as f:
            return json.load(f)

    def load_state(self):
        self.action = []
        self.args = {}
        data = self.get_state()
        if data is None:
            return
        action = self.action_manager.action_deserialize(data['action'])
        self.args = data['args']
        self.action = action

    def load_state_safe(self):
        try:
            self.load_state()
        except Exception as ex:
            print("Error loading state file '%s':\n    %s" %
                  (self.state_file_path, ex))
            cnf = input("Do you want to delete this (likely corrupt) "
                        "state file? [Yn] ")
            if cnf == '' or cnf.lower() == 'y':
                os.remove(self.state_file_path)
                print("State file removed.")
            else:
                raise

    def clear_state(self, state_file=True, verbose=False):
        self.action = []
        self.args = {}
        if state_file and os.path.isfile(self.state_file_path):
            os.remove(self.state_file_path)
            if verbose:
                print("State file removed.")

    def _new_action_check(self, new_action):
        if not new_action.continuable:
            # only actions that save state care about state
            return
        state = self.get_state()
        if state:
            action_name = state['action'][0]
            print(log.term.important(
                  "You're in the middle of previous action: %s\n" %
                  action_name))
            print((
                " a) View status of previous action:\n"
                "    {t.cmd}rdopkg status{t.normal}\n\n"
                " b) Continue the previous action:\n"
                "    {t.cmd}rdopkg --continue{t.normal} / "
                "{t.cmd}rdopkg -c{t.normal}\n\n"
                " a) Abort the previous action:\n"
                "    {t.cmd}rdopkg --abort{t.normal}"
            ).format(t=log.term))
            raise exception.ActionInProgress(action=action_name)

    def new_action(self, action, args=None):
        new_action = None
        new_args = {}
        if isinstance(action, _action.Action):
            new_action = action
        else:
            for a in self.action_manager.actions:
                if a.name == action:
                    new_action = a
                    break
        if not new_action:
            raise exception.InvalidAction(action=action)
        if new_action.alias:
            for a in self.action_manager.actions:
                if a.name == new_action.alias:
                    # const_args of alias action are passed as args
                    new_args = new_action.const_args or {}
                    new_action = a
                    break
        self._new_action_check(new_action)
        self.action = [new_action]
        if args:
            new_args.update(args)
        self.args = new_args

        if not new_action.continuable and new_action.steps:
            self.save_state()

    def print_progress(self):
        if not self.action:
            return

        def _print_steps(steps, current, indent=1, done=True):
            if current:
                _current = current[0]
            else:
                _current = []
            found_current = False
            for step in steps:
                next_current = []
                if done and step == _current:
                    next_current = current[1:]
                    found_current = True
                    schar = '*'
                elif done:
                    schar = 'x'
                else:
                    schar = ' '
                print("%s[%s] %s" % (indent * "  ", schar, step.name))
                if step.steps:
                    _print_steps(step.steps, next_current,
                                 indent=indent + 1, done=done)
                if found_current:
                    done = False

        _print_steps([self.action[0]], self.action)

    def status(self):
        if self.action:
            print(
                "{t.bold}Action in progress: {t.green}{a}{t.normal}\n".format(
                    t=log.term, a=self.action[0].name))
            if self.args:
                print(log.term.bold("Arguments:"))
                for key in sorted(self.args, key=self.args.get):
                    print("  %s: %s" % (key, self.args[key]))
                print(log.term.bold("\nProgress:"))
                self.print_progress()
            else:
                print(log.term.bold("No arguments.\n"))
        else:
            print(log.term.bold("No action in progress."))

    def check_actions(self):
        fails = []

        def _check_action(a, indent=''):
            s = "%s%s: %s" % (indent, a.module, a.name)
            if a.steps:
                print(s)
                for s in a.steps:
                    _check_action(s, indent + '  ')
            else:
                action_fun = self.action_manager._get_action_fun(a)
                if not action_fun:
                    s += ' {t.red_bold}NOT AVAILABLE{t.normal}'.format(
                        t=log.term)
                    fails.append(a)
                print(s)

        for a in self.action_manager.actions:
            _check_action(a)
        return fails

    def engage(self):
        if not self.action:
            raise exception.NoActionInProgress
        continuable = self.action[0].continuable

        def _save_state():
            if continuable:
                self.save_state()
        self.action_manager.ensure_leaf_action(self.action,
                                               on_change_callback=_save_state)

        abort = False
        while self.action:
            new_args = None
            select_next = True
            step = self.action[-1]
            try:
                new_args = self.action_manager.run_action(step, self.args)
            except exception.ActionRequired as ex:
                helpers.action_required(str(ex))
                new_args = ex.kwargs.get('args', None)
                select_next = not ex.kwargs.get('rerun', False)
                abort = True
            except exception.ActionFinished as ex:
                self.clear_state(state_file=continuable)
                print(ex)
                return
            except exception.ActionGoto as ex:
                # Here be dragons.
                select_next = False
                new_args = ex.kwargs.get('args', None)
                goto = [self.action[0].name] + ex.kwargs['goto']
                self.action = self.action_manager.action_deserialize(goto)
            if new_args:
                self.args.update(new_args)
            if select_next:
                self.action = self.action_manager.next_action(self.action)
            if not self.action:
                if continuable:
                    print("Action finished.")
                self.clear_state(state_file=continuable)
                return
            if continuable:
                self.save_state()
            if abort:
                return
