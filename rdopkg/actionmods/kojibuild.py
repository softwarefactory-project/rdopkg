"""
Because fedpkg/pyrpkg sucks horribly, this entire file full of hacks is
needed to interface with it. Disgusting.
"""
from __future__ import print_function
from six.moves import configparser
import logging
import sys
import os

from rdopkg import exception
from rdopkg.utils.log import log


KOJI_AVAILABLE = False
try:
    import koji  # NOQA
    KOJI_AVAILABLE = True
except ImportError:
    pass

FEDPKG_AVAILABLE = False
try:
    import fedpkg
    FEDPKG_AVAILABLE = True
except ImportError:
    pass


KOJI_HUB_URL = 'http://koji.fedoraproject.org/kojihub'
KOJI_BASE_URL = 'http://kojipkgs.fedoraproject.org/work/'


def modules_check():
    if not KOJI_AVAILABLE:
        raise exception.ModuleNotAvailable(module='koji')
    if not FEDPKG_AVAILABLE:
        raise exception.ModuleNotAvailable(module='fedpkg')


def setup_fedpkg_logger():
    flog = logging.getLogger('rpkg')
    fmtr = logging.Formatter('%(message)s')
    for h in list(flog.handlers):
        flog.removeHandler(h)
    stdouth = logging.StreamHandler(sys.stdout)
    stdouth.setFormatter(fmtr)
    flog.addHandler(stdouth)
    flog.setLevel(logging.INFO)
    return flog


def get_fedpkg_config():
    fedpkg_conf = '/etc/rpkg/fedpkg.conf'
    config = configparser.SafeConfigParser()
    config.read(fedpkg_conf)
    return config


def get_fedpkg_commands():
    config = get_fedpkg_config()
    items = dict(config.items('fedpkg', raw=True))
    # I don't even...
    cmd = fedpkg.Commands(os.getcwd(),
                          items['lookaside'],
                          items['lookasidehash'],
                          items['lookaside_cgi'],
                          items['gitbaseurl'],
                          items['anongiturl'],
                          items['branchre'],
                          items['kojiconfig'],
                          items['build_client'],
                          )
    return cmd


class FedpkgArgsStub(object):
    """
    fedpkg sucks, this is one of many results
    """

    def __init__(self):
        self.q = False


def get_fedpkg_cli(config=None, flog=None):
    if not config:
        config = get_fedpkg_config()
    if not flog:
        flog = logging.getLogger('rpkg')
    cli = fedpkg.cli.cliClient(config)
    cli.log = flog
    cli.args = cli.args = FedpkgArgsStub()
    return cli


def new_build(watch=True):
    modules_check()
    flog = setup_fedpkg_logger()  # NOQA
    fcmd = get_fedpkg_commands()
    task_id = fcmd.build()

    if watch:
        print('')
        try:
            cli = get_fedpkg_cli()
            # TODO: might be good to push this return data back up
            #       or check the status of the return
            r = cli._watch_koji_tasks(fcmd.kojisession, [task_id])
        except configparser.NoSectionError:
            # <C-C> causes this for some reason
            print('')
        except Exception as ex:
            log.warn(str(type(ex).__name__))
            log.warn("Failed to get build status: %s" % ex)

    return fcmd.nvr
