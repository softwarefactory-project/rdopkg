"""
This module implement generic support of Koji through Koji ugly API.
For now, it's only used for CBS.
"""
from __future__ import print_function
from distutils.spawn import find_executable
import os
import subprocess

from rdopkg.exception import ModuleNotAvailable, RpmModuleNotAvailable
from rdopkg.utils.specfile import spec_fn, Spec
from rdopkg.utils.log import log
from rdopkg import exception, guess

from munch import munchify

KOJI_AVAILABLE = False
try:
    import koji
    KOJI_AVAILABLE = True
except ImportError:
    pass
RPM_AVAILABLE = False
try:
    import rpm
    RPM_AVAILABLE = True
except ImportError:
    pass


def setup_kojiclient(profile):
    """Setup koji client session
    """
    opts = koji.read_config(profile)
    for k, v in opts.iteritems():
        opts[k] = os.path.expanduser(v) if type(v) is str else v
    kojiclient = koji.ClientSession(opts['server'], opts=opts)
    kojiclient.ssl_login(opts['cert'], None, opts['serverca'])
    return kojiclient


def new_build(profile='cbs', scratch=True):
    # Very ugly: some utilities are only available in koji CLI
    # and not in the koji module
    if not KOJI_AVAILABLE:
        raise ModuleNotAvailable(module='koji')
    if not RPM_AVAILABLE:
        raise RpmModuleNotAvailable()
    import imp
    kojibin = find_executable('koji')
    kojicli = imp.load_source('kojicli', kojibin)
    # Koji 1.13 moves client internal API into another path
    try:
        from koji_cli.lib import _unique_path, _progress_callback, watch_tasks
    except ImportError:
        from kojicli import _unique_path, _progress_callback, watch_tasks

    kojiclient = setup_kojiclient(profile)
    # Note: required to make watch_tasks work
    kojicli.options = opts = munchify(kojiclient.opts)
    build_target = guess_build()
    if not build_target:
        log.warn("failed to identify build tag from branch")
        return

    retrieve_sources()
    srpm = create_srpm()
    if not srpm:
        log.warn('No srpm available')
        return
    serverdir = _unique_path('cli-build')
    kojiclient.uploadWrapper(srpm, serverdir, callback=_progress_callback)
    source = "%s/%s" % (serverdir, os.path.basename(srpm))
    task_id = kojiclient.build(source, build_target, {'scratch': scratch})
    print("Created task:", task_id)

    print("Task info: {}/taskinfo?taskID={}".format(opts['weburl'], task_id))
    kojiclient.logout()
    watch_tasks(kojiclient, [task_id])


def guess_build():
    release = guess.osrelease()
    builds = guess.builds(release)
    if builds:
        build_tag = builds[0][1].replace('cbs/', '')
        return build_tag
    return None


def retrieve_sources():
    """Retrieve sources using spectool
    """
    spectool = find_executable('spectool')
    if not spectool:
        log.warn('spectool is not installed')
        return
    try:
        specfile = spec_fn()
    except Exception:
        return

    cmd = [spectool, "-g", specfile]
    output = subprocess.check_output(' '.join(cmd), shell=True)
    log.warn(output)


def create_srpm(dist='el7'):
    """Create an srpm
    Requires that sources are available in local directory

    dist: set package dist tag (default: el7)
    """
    if not RPM_AVAILABLE:
        raise RpmModuleNotAvailable()
    path = os.getcwd()
    try:
        specfile = spec_fn()
        spec = Spec(specfile)
    except Exception:
        return

    rpmdefines = ["--define 'dist .{}'".format(dist),
                  "--define '_sourcedir {}'".format(path),
                  "--define '_srcrpmdir {}'".format(path)]
    rpm.addMacro('_sourcedir', '.{}'.format(dist))
    # FIXME: needs to be fixed in Spec
    rpm.addMacro('dist', '.{}'.format(dist))
    module_name = spec.get_tag('Name', True)
    version = spec.get_tag('Version', True)
    release = spec.get_tag('Release', True)
    srpm = os.path.join(path,
                        "{}-{}-{}.src.rpm".format(module_name,
                                                  version,
                                                  release))

    # See if we need to build the srpm
    if os.path.exists(srpm):
        log.warn('Srpm found, rewriting it.')

    cmd = ['rpmbuild']
    cmd.extend(rpmdefines)

    cmd.extend(['--nodeps', '-bs', specfile])
    output = subprocess.check_output(' '.join(cmd), shell=True)
    log.warn(output)
    srpm = output.split()[1]
    return srpm
