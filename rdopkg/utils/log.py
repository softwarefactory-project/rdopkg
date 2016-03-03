import logging

import terminal


INFO = logging.INFO
# between info and debug
VERBOSE = (logging.INFO + logging.DEBUG) / 2
DEBUG = logging.DEBUG

log = logging.getLogger('rdopkg')
log.setLevel(logging.INFO)
if len(log.handlers) < 1:
    formatter = logging.Formatter(fmt='%(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log.addHandler(handler)


class LogTerminal(terminal.Terminal):
    @property
    def warn(self):
        return self.yellow

    @property
    def important(self):
        return self.yellow_bold

    @property
    def error(self):
        return self.red

    @property
    def good(self):
        return self.green

    @property
    def cmd(self):
        return self.cyan


term = LogTerminal()


def set_colors(colors):
    global term
    if colors == 'yes':
        if not terminal.COLOR_TERMINAL:
            return False
        term = LogTerminal(force_styling=True)
        return True
    elif colors == 'no':
        if not terminal.COLOR_TERMINAL:
            return True
        term = LogTerminal(force_styling=None)
        return True
    elif colors == 'auto':
        term = LogTerminal()
        return True
    return False


def error(*args, **kwargs):
    if args:
        largs = list(args)
        largs[0] = term.error(args[0])
        args = tuple(largs)
    log.error(*args, **kwargs)


def warn(*args, **kwargs):
    if args:
        largs = list(args)
        largs[0] = term.warn(args[0])
        args = tuple(largs)
    log.warning(*args, **kwargs)


def success(*args, **kwargs):
    if args:
        largs = list(args)
        largs[0] = term.good(args[0])
        args = tuple(largs)
    log.info(*args, **kwargs)


def info(*args, **kwargs):
    log.info(*args, **kwargs)


def verbose(*args, **kwargs):
    log.log(VERBOSE, *args, **kwargs)


def debug(*args, **kwargs):
    log.debug(*args, **kwargs)


def command(*args, **kwargs):
    log.info(*args, **kwargs)
