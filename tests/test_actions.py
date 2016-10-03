from rdopkg.cli import rdopkg


def test_actions_availability():
    r = rdopkg('actions')
    assert r == 0, "Some action functions are NOT AVAILABLE"


def test_actions_continue_short():
    r = rdopkg('-c')
    assert r == 1, "-c succeeded with no state"


def test_actions_continue_long():
    r = rdopkg('--continue')
    assert r == 1, "--continue succeeded with no state"
