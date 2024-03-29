# -*- coding: utf-8 -*-

import errno
import glob
import importlib
import os.path


class Config(dict):

    def __init__(self, defaults=None):
        dict.__init__(self, defaults or {})

    def from_pyfile(self, filename, silent=False):
        d = importlib.new_module('extconfig')
        d.__file__ = filename
        try:
            with open(filename) as config_file:
                exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
        except IOError as e:
            if silent and e.errno in (errno.ENOENT, errno.EISDIR):
                return False
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        self.from_object(d)
        return True

    def from_object(self, o):
        for key in dir(o):
            if key.isupper():
                self[key] = getattr(o, key)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, dict.__repr__(self))


cfg = Config({
    'HOME_DIR': os.path.expanduser("~/.rdopkg"),
    'RDOINFO_FILE': 'rdo-full.yml',
    'DISTRO': 'RDO',
    'RDOINFO_REPO': 'https://github.com/redhat-openstack/rdoinfo.git',
    'RDOINFO_RAW_URL': ('https://raw.githubusercontent.com/'
                        'redhat-openstack/rdoinfo/master/'),
    'FETCH_PERIOD': 600,
    'REQCHECK_PY_VERSION': '3.9',
})
cfg_files = []


def get_config_fns():
    home_glob = cfg['HOME_DIR'] + '/conf.d/*.py'
    fns = glob.glob('/etc/rdopkg.d/*.py') + glob.glob(home_glob)
    return fns


def load_config():
    for cfn in get_config_fns():
        cfg.from_pyfile(cfn)
        cfg_files.append(cfn)


load_config()
