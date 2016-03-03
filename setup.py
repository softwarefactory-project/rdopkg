#!/usr/bin/env python

import re
import setuptools
from rdopkg import __version__


def requires():
    try:
        reqs = map(str.strip, open('requirements.txt').readlines())
        reqs = filter(lambda s: re.match('\w', s), reqs)
        return reqs
    except Exception:
        pass
    return []


setuptools.setup(
    name='rdopkg',
    version=__version__,
    description='RDO packaging utility',
    author='Jakub Ruzicka',
    author_email='jruzicka@redhat.com',
    url='https://github.com/redhat-openstack/rdopkg',
    packages=['rdopkg', 'rdopkg.utils', 'rdopkg.actionmods', 'rdopkg.gerrit'],
    install_requires=requires(),
    entry_points={
        "console_scripts": ["rdopkg = rdopkg.shell:main"]
    }
)
