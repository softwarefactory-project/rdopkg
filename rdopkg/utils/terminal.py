class NullCallableString(unicode):
    """
    This emulates blessings class of same for cases when blessings aren't
    available
    """
    def __new__(cls):
        return unicode.__new__(cls, u'')

    def __call__(self, arg, *extra_args):
        if isinstance(arg, int):
            return u''
        return arg


class PlainTerminal(object):
    """
    Mock of blessings Terminal that ignores fromatting
    """
    nullstr = NullCallableString()

    def __getattr__(self, attr):
        setattr(self, attr, self.nullstr)
        return self.nullstr


COLOR_TERMINAL = False
try:
    import blessings
    COLOR_TERMINAL = True
    Terminal = blessings.Terminal
except ImportError:
    Terminal = PlainTerminal
