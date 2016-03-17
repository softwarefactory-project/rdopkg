# -*- encoding: utf-8 -*-

import json
import os

import action as _action
import actions
import const
import exception
import helpers
from utils import log


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
        if self.action and self.action[0].atomic:
            # don't save state for atomic actions
            return
        data = {
            'action': self.action_manager.action_serialize(self.action),
            'args': self.args
        }
        sf = file(self.state_file_path, 'wt')
        json.dump(data, sf)
        sf.close()

    def load_state(self):
        self.action = []
        self.args = {}
        if not os.path.isfile(self.state_file_path):
            return
        sf = file(self.state_file_path, 'rt')
        data = json.load(sf)
        action = self.action_manager.action_deserialize(data['action'])
        self.args = data['args']
        self.action = action
        sf.close()

    def load_state_safe(self):
        try:
            self.load_state()
        except Exception as ex:
            print("Error loading state file '%s':\n    %s" %
                  (self.state_file_path, ex))
            cnf = raw_input("Do you want to delete this (likely corrupt) "
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
        if self.action and not new_action.atomic:
            action_name = self.action[0].name
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
            ).format(t=log.term)
            )
            raise exception.ActionInProgress(action=action_name)

    def new_action(self, action, args=None):
        self._new_action_check(action)
        if args:
            self.args = args
        if isinstance(action, _action.Action):
            self.action = [action]
        else:
            self.action = []
            for a in self.action_manager.actions:
                if a.name == action:
                    self.action = [a]
                    break
        if not self.action:
            raise exception.InvalidAction(action=action)
        if not action.atomic and action.steps:
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

    def engage(self):
        if not self.action:
            raise exception.NoActionInProgress
        atomic = self.action[0].atomic

        def _save_state():
            if not atomic:
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
                self.clear_state(state_file=not atomic)
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
                if not atomic:
                    print("Action finished.")
                self.clear_state(state_file=not atomic)
                return
            if not atomic:
                self.save_state()
            if abort:
                return
