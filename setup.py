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
    url='https://github.com/openstack-packages/rdopkg',
    # TODO: find better solution than maintaining this redundant list by hand
    packages=[
        'rdopkg',
        'rdopkg.utils',
        'rdopkg.actionmods',
        'rdopkg.actions',
        'rdopkg.actions.build',
        'rdopkg.actions.distgit',
        'rdopkg.actions.reqs',
        'rdopkg.actions.review',
        'rdopkg.actions.util',
    ],
    install_requires=requires(),
    entry_points={
        "console_scripts": ["rdopkg = rdopkg.cli:main"]
    }
)
