from rdopkg import helpers
from rdopkg import exception
import pytest


def test_editor_editor_run_failed(monkeypatch):

    def mock_run(*args, **kwargs):
        raise exception.CommandNotFound('Foo')
    monkeypatch.setattr(helpers, 'run', mock_run)

    def mock_env(var):
        return 'foo_editor'

    with pytest.raises(exception.CommandNotFound) as excinfo:
        helpers.edit('/tmp/foo')
    print excinfo
    assert False


def test_editor_no_env(monkeypatch):

    def mock_run(*args, **kwargs):
        raise exception.CommandNotFound('Foo')
    monkeypatch.setattr(helpers, 'run', mock_run)

    def mock_env(var):
        return ''

    with pytest.raises(exception.CommandNotFound) as excinfo:
        helpers.edit('/tmp/foo')
    print excinfo
    assert False
