from __future__ import print_function
from distroinfo.info import DistroInfo

from rdopkg.actionmods import rdoinfo
from rdopkg import helpers


def release(release_specified=None, local_info=None, info_file=None):
    if not info_file:
        info_file = rdoinfo.info_file()
    if local_info:
        di = DistroInfo(info_file,
                        local_info=local_info)
    else:
        di = rdoinfo.get_distroinfo()
    info = di.get_info()
    releases = info['releases']
    if not release_specified:
        for release in releases:
            rdoinfo.print_release_info(release)
            print()
    else:
        for release in releases:
            if release["name"] == release_specified:
                rdoinfo.print_release_info(release)
                break
        else:
            print("No release match your filter.")
