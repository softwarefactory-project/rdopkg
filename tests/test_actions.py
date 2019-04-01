import pytest

from rdopkg.cli import rdopkg, rdopkg_runner
from rdopkg import exception

import actions


def test_actions_availability():
    r = rdopkg('actions')
    assert r == 0, "Some action functions are NOT AVAILABLE"


def test_actions_continue_short():
    r = rdopkg('-c')
    assert r == 1, "-c succeeded with no state"


def test_actions_continue_long():
    r = rdopkg('--continue')
    assert r == 1, "--continue succeeded with no state"


def test_duplicate_action():
    runner = rdopkg_runner()
    aman = runner.action_manager
    with pytest.raises(exception.DuplicateAction):
        aman.add_actions_modules(actions, override=False)


def test_action_override():
    runner = rdopkg_runner()
    aman = runner.action_manager
    aman.add_actions_modules(actions, override=True)
    found = False
    for action in aman.actions:
        if action.name == 'clone':
            # make sure clone action is overridden with the custom one
            assert action.module == 'foomod'
            found = True
            break
    assert found, "clone action not found ?!"
