from rdopkg.utils.exception import CommandFailed
from rdopkg.utils.exception import RdopkgException


def test_exception_Default():
    e = RdopkgException()
    assert str(e) == 'An unknown error occurred'


def test_exception_msg_provided():
    e = RdopkgException(msg='foo bar')
    assert str(e) == 'foo bar'


def test_CommandFailed_bad_kwargs():
    e = CommandFailed(foo='bar')
    assert str(e) == e.msg_fmt


def test_CommandFailed_good_kwargs():
    e = CommandFailed(cmd='bar')
    assert str(e) == e.msg_fmt % {'cmd': 'bar'}
