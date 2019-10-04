# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import json
import six
import subprocess

from rdopkg import exception
from rdopkg.utils import log


class _CommandOutput(six.text_type):
    """
    Just a string subclass with attribute access.
    """
    @property
    def success(self):
        return self.return_code == 0


def encode(s, encoding='utf-8'):
    """
    Compat: encode PY2 unicode to str on PY2 only.
    """
    if six.PY2 and isinstance(s, unicode):
        return s.encode(encoding=encoding)
    return s


def log_cmd_fail(cmd, cout, fail_log_fun=log.warn, out_log_fun=log.info):
    fail_log_fun('{t.error}command failed: {t.normal}{t.cmd}{cmd}{t.normal}'
                 .format(t=log.term, cmd=cmd))
    nl = False
    if cout:
        out_log_fun(log.term.bold("stdout:"))
        out_log_fun(cout)
        nl = True
    if cout.stderr:
        out_log_fun(log.term.bold("stderr:"))
        out_log_fun(cout.stderr)
        nl = True
    if nl:
        out_log_fun('')


def run(cmd, *params, **kwargs):
    fatal = kwargs.get('fatal', True)
    direct = kwargs.get('direct', False)
    log_cmd = kwargs.get('log_cmd', True)
    log_fail = kwargs.get('log_fail', True)
    input = kwargs.get('input')
    print_stdout = kwargs.get('print_stdout', False)
    print_stderr = kwargs.get('print_stderr', False)
    print_output = kwargs.get('print_output', False)
    env = kwargs.get('env', None)

    cmd = [cmd]
    cmd.extend(p if isinstance(p, six.string_types) else six.text_type(p)
               for p in params)
    cmd_str = ' '.join(cmd)

    if log_cmd:
        log.command(log.term.cmd(cmd_str))

    if print_output:
        print_stdout = True
        print_stderr = True

    if input:
        stdin = subprocess.PIPE
        input = input.encode('utf-8')
    else:
        stdin = None

    if direct:
        stdout = None
        stderr = None
    else:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE

    cmd = list(map(encode, cmd))
    try:
        prc = subprocess.Popen(cmd, stdin=stdin, stdout=stdout,
                               stderr=stderr, env=env)
    except OSError:
        raise exception.CommandNotFound(cmd=cmd[0])
    out, err = prc.communicate(input=input)

    if out:
        out = out.rstrip()
        if print_stdout:
            log.info(out)
    else:
        out = b''

    if err:
        err = err.rstrip()
        if print_stderr:
            log.info(err)
    else:
        err = b''

    cout = _CommandOutput(out.decode('utf-8'))
    cout.stderr = err
    cout.return_code = prc.returncode
    cout.cmd = cmd_str
    if prc.returncode != 0:
        if log_fail:
            log_cmd_fail(cmd_str, cout)
        if fatal:
            raise exception.CommandFailed(cmd=cmd, out=cout)
    return cout


class ShellCommand(object):
    command = None

    def __init__(self):
        if self.command is None:
            self.command = self.__class__.__name__.lower()

    def __call__(self, *params, **kwargs):
        return run(self.command, *params, **kwargs)


class GerritQuery(ShellCommand):
    def __init__(self, host, port, log_cmd=True):
        self.host = host
        self.port = port
        self.log_cmd = log_cmd

    def __call__(self, *params, **kwargs):
        if 'log_cmd' not in kwargs:
            kwargs['log_cmd'] = self.log_cmd
        results = run('ssh', '-p', self.port, self.host,
                      'gerrit', 'query', '--format=JSON',
                      *params, **kwargs)
        # gerrit sends stats that we need to discard
        result = results.split('}\n{')[0]
        try:
            j = json.loads(result + '}')
        except ValueError:
            j = json.loads(result)
        if j.get('type') in ['error', 'stats']:
            # we have no results, just the query stats
            return None
        else:
            return j
