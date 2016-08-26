"""
This module implement generic support of Koji through Koji ugly API.
For now, it's only used for CBS.
"""
from distutils.spawn import find_executable
import os
import subprocess

from rdopkg.utils.specfile import spec_fn, Spec
from rdopkg.utils.log import log
from rdopkg import guess


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


options = None


class KojiOpts(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            if type(v) is str:
                v = os.path.expanduser(v)
            setattr(self, k, v)


def new_build(profile='cbs', scratch=True):
    # Very ugly: some utilities are only available in koji CLI
    # and not in the koji module
    if not KOJI_AVAILABLE:
        raise exception.ModuleNotAvailable(module='koji')
    if not RPM_AVAILABLE:
        raise exception.ModuleNotAvailable(module='rpm')
    import imp
    kojibin = find_executable('koji')
    kojicli = imp.load_source('kojicli', kojibin)
    from kojicli import _unique_path, _progress_callback, watch_tasks

    build_target = guess_build()
    if not build_target:
        log.warn("failed to identify build tag from branch")
        return
    options = koji.read_config(profile)
    opts = KojiOpts(**options)
    # Note: required to make watch_tasks work
    kojicli.options, weburl = opts, opts.weburl
    kojiclient = koji.ClientSession(opts.server)
    kojiclient.ssl_login(opts.cert, None, opts.serverca)
    retrieve_sources()
    srpm = create_srpm()
    opts = {'scratch': scratch}
    if not srpm:
        log.warn('No srpm available')
        return
    serverdir = _unique_path('cli-build')
    kojiclient.uploadWrapper(srpm, serverdir, callback=_progress_callback)
    source = "%s/%s" % (serverdir, os.path.basename(srpm))
    task_id = kojiclient.build(source, build_target, opts)
    print "Created task:", task_id

    print "Task info: {}/taskinfo?taskID={}".format(weburl, task_id)
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
    except:
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
        raise exception.ModuleNotAvailable(module='rpm')
    path = os.getcwd()
    try:
        specfile = spec_fn()
        spec = Spec(specfile)
    except:
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
