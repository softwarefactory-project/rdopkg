from rdopkg import helpers
from rdopkg import exception
import pytest


@pytest.mark.skip('Temporarily diabled during migration to sf.')
def test_editor_editor_run_failed(monkeypatch):

    def mock_run(*args, **kwargs):
        raise exception.CommandNotFound('Foo')
    monkeypatch.setattr(helpers, 'run', mock_run)

    def mock_env(var):
        return 'foo_editor'
    monkeypatch.setattr(helpers.os.environ, 'get', mock_env)

    with pytest.raises(exception.CommandNotFound) as excinfo:
        helpers.edit('/tmp/foo')
    assert excinfo.match(r'.*\(foo_editor\).* Please set \$EDITOR .*')


@pytest.mark.skip('Temporarily diabled during migration to sf.')
def test_editor_no_env(monkeypatch):

    def mock_run(*args, **kwargs):
        raise exception.CommandNotFound('Foo')
    monkeypatch.setattr(helpers, 'run', mock_run)

    def mock_env(var):
        return ''
    monkeypatch.setattr(helpers.os.environ, 'get', mock_env)

    with pytest.raises(exception.CommandNotFound) as excinfo:
        helpers.edit('/tmp/foo')
    assert excinfo.match(r'.*\(vim\).* Please set \$EDITOR .*')
