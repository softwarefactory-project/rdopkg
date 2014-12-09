#!/usr/bin/env python

import setuptools
from rdopkg import VERSION


setuptools.setup(
    name='rdopkg',
    version=VERSION,
    description='RDO packaging utility',
    author='Jakub Ruzicka',
    author_email='jruzicka@redhat.com',
    url='https://github.com/redhat-openstack/rdopkg',
    packages=['rdopkg', 'rdopkg.utils', 'rdopkg.actionmods', 'rdopkg.gerrit'],
    entry_points={
        "console_scripts": ["rdopkg = rdopkg.shell:main"]
    }
)
