#!/usr/bin/env python
"""
An example script that uses rdopkg.actionmods.rdoinfo to output a list of
currently maintained RDO projects.
"""

from rdopkg.actionmods import rdoinfo


def list_projects():
    inforepo = rdoinfo.get_default_inforepo()
    info = inforepo.get_info()
    pkgs = info['packages']

    pkg_filter = {
        'name': '^openstack-'
    }
    pkgs = rdoinfo.filter_pkgs(pkgs, pkg_filter)

    for pkg in pkgs:
        project = pkg.get('project') or pkg['name']
        print("### " + project)
        print("package: " + pkg['name'])
        print("code: " + pkg.get('upstream', 'N/A'))
        print("maintainers: " + " ".join(pkg['maintainers']))
        print("")


if __name__ == '__main__':
    list_projects()
