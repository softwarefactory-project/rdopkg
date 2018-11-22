from __future__ import print_function
import contextlib
import os
import re
import six
from six.moves import input
from six import string_types
import sys
import yaml

from rdopkg import exception
from rdopkg.utils import log
from rdopkg.utils.cmd import run

if six.PY2:
    from collections import Iterable
else:
    from collections.abc import Iterable


def confirm(msg, default_yes=True):
    if sys.stdout.isatty():
        if default_yes:
            options = '[Yn]'
        else:
            options = '[Ny]'
        print('')
        i = input(log.term.important("%s %s " % (msg, options))).lower()
        if not i:
            if default_yes:
                return
            else:
                raise exception.UserAbort()
        if i != 'y' and i != 'yes':
            raise exception.UserAbort()
        print('')
    else:
        if default_yes:
            return
        else:
            raise exception.UserAbort()


def download_file(url):
    run('curl', '-L', '-f', '-O', url, direct=True)


def edit(path):
    editor = os.environ.get('EDITOR')
    if not editor:
        editor = 'vim'
        log.info("$EDITOR not set. Falling back to %s." % editor)
    try:
        r = run(editor, path, direct=True)
    except exception.CommandNotFound:
        raise exception.CommandNotFound(
            msg='Failed to find suitable text editor ({0}).  '
                'Please set $EDITOR environment variable.'.format(editor))
    return r.success


def ensure_dir(path):
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise exception.NotADirectory(path=path)
    else:
        os.makedirs(path)


def ensure_new_file_dirs(path):
    if path[-1] == os.sep:
        raise exception.NotAFile(path=path)
    _dir = os.path.dirname(path)
    if _dir:
        ensure_dir(_dir)


def find_files(path, ext=None):
    paths = [os.path.join(path, f) for f in os.listdir(path)
             if os.path.isfile(os.path.join(path, f))]
    if ext:
        paths = [p for p in paths if p.endswith(ext)]
    return paths


def print_list(l, pre='- ', nl_before=False, nl_after=False):
    if nl_before:
        print("")
    for e in l:
        print('%s%s' % (pre, e))
    if nl_after:
        print("")


def action_required(msg):
    print("\n{t.important}Action required: {t.normal}{t.bold}{msg}{t.normal}"
          .format(t=log.term, msg=msg))
    print("\nOnce done, run `rdopkg -c` to continue.\n")


def is_same_hash(h1, h2):
    if h1 is None or h2 is None:
        return False
    if h1 == h2 or h1.startswith(h2) or h2.startswith(h1):
        return True
    return False


def strip_patch_subject(subj):
    return re.sub(r'^\[PATCH\]\s+', '', subj.strip())


def is_same_subject(s1, s2):
    if s1 is None or s2 is None:
        return False
    if strip_patch_subject(s1) == strip_patch_subject(s2):
        return True
    return False


@contextlib.contextmanager
def cdir(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@contextlib.contextmanager
def setenv(**env_dict):
    orig_env = os.environ.copy()
    for k, v in env_dict.items():
        os.environ[k] = str(v)
    try:
        yield
    finally:
        for k, v in env_dict.items():
            del os.environ[k]
        for k, v in orig_env.items():
            os.environ[k] = v


def print_keyval(key, val, kb=True, vb=False):
    if kb:
        fmt = '{t.bold}{key}{t.normal}: '
    else:
        fmt = '{key}'
    if vb:
        fmt += '{t.bold}{val}{t.bold}'
    else:
        fmt += '{val}'
    if not isinstance(
            val,
            string_types) and isinstance(
            val,
            Iterable):
        vals = "\n" + "\n".join(map(lambda x: '- ' + str(x), val))
    else:
        vals = str(val)
    print(fmt.format(t=log.term, key=key, val=vals))


class DictPrinter(object):
    # Very simple and stupid dict printer.

    def __init__(self, header=None, first=None, last=None):
        self.first = first or []
        self.last = last or []
        self.header = header

    def __call__(self, d):
        dd = d.copy()
        # print header
        if self.header:
            hdr = dd.pop(self.header, '')
            print_keyval(self.header, hdr, kb=True, vb=True)
        # print first fields
        for key in self.first:
            if key not in dd:
                continue
            val = dd.pop(key)
            print_keyval(key, val)
        # filter out last fields
        last_items = []
        for key in self.last:
            if key not in dd:
                continue
            last_items.append((key, dd.pop(key)))
        if dd:
            print(yaml.dump(dd, default_flow_style=False).rstrip())
        for key, val in last_items:
            print_keyval(key, val)
