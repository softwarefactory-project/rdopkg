from rdopkg.utils.exception import CommandFailed
from rdopkg.utils.exception import RdopkgException


def test_exception_Default():
    e = RdopkgException()
    assert str(e) == 'An unknown error occurred'
    assert e.exit_code == 1


def test_exception_msg_provided():
    e = RdopkgException(msg='foo bar')
    assert str(e) == 'foo bar'


def test_CommandFailed_bad_kwargs():
    e = CommandFailed(foo='bar')
    assert str(e) == e.msg_fmt


def test_CommandFailed_good_kwargs():
    e = CommandFailed(cmd='bar')
    assert str(e) == e.msg_fmt % {'cmd': 'bar'}


def test_exception_exit_code():
    MAGIC_CODE = 42
    e = RdopkgException(exit_code=MAGIC_CODE)
    assert e.exit_code == MAGIC_CODE
