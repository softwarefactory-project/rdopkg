from rdopkg.cli import rdopkg


def test_actions_availability():
    r = rdopkg('actions')
    assert r == 0, "Some action functions are NOT AVAILABLE"
