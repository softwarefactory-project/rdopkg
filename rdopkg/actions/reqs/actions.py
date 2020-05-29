"""
Requirements related actions.
"""
from __future__ import print_function
import os
import re
import yaml

from rdopkg import exception
from rdopkg import guess
from rdopkg.actionmods import query as _query
from rdopkg.actionmods import reqs as _reqs
from rdopkg.utils import log
from rdopkg.utils import specfile
from rdopkg.utils.git import git


def reqdiff(version_tag_from, version_tag_to):
    fmt = "\n{t.bold}requirements.txt diff{t.normal} between " \
          "{t.bold}{old}{t.normal} and {t.bold}{new}{t.normal}:"
    log.info(fmt.format(t=log.term, old=version_tag_from, new=version_tag_to))
    rdiff = _reqs.reqdiff_from_refs(version_tag_from, version_tag_to)
    _reqs.print_reqdiff(*rdiff)


def reqcheck(version, python_version='3.6', override=None):
    m = re.search(r'^[\d]\.[\d]$', python_version)
    if not m:
        raise exception.WrongPythonVersion()

    override_pkgs = None
    if override:
        try:
            with open(override, 'r') as override_file:
                override_pkgs = yaml.load(override_file,
                                          Loader=yaml.SafeLoader)
        except Exception as e:
            e.strerror = 'Unable to load the override file (%s)' % e.strerror
            raise

    if version.upper() == 'XXX':
        if 'upstream' in git.remotes():
            current_branch = git.current_branch()
            branch = current_branch.replace('rpm-', '')
            if branch != 'master':
                branch = 'stable/{}'.format(branch)
            version = 'upstream/{}'.format(branch)
            check = _reqs.reqcheck_spec(python_version,
                                        ref=version,
                                        override_pkgs=override_pkgs)
        else:
            m = re.search(r'/([^/]+)_distro', os.getcwd())
            if not m:
                raise exception.CantGuess(what="requirements.txt location",
                                          why="failed to parse current path")
            path = '../%s/requirements.txt' % m.group(1)
            log.info("Delorean detected. Using %s" % path)
            check = _reqs.reqcheck_spec(python_version,
                                        reqs_txt=path,
                                        ref=version,
                                        override_pkgs=override_pkgs)
    else:
        check = _reqs.reqcheck_spec(python_version,
                                    ref=version,
                                    override_pkgs=override_pkgs)
    return {'check': check}


def reqcheck_autosync(check=None, autosync=False):
    if not autosync:
        return
    spec = specfile.Spec()
    met, any_version, wrong_version, missing, excess, removed = check
    main_py_subpkg = spec.guess_main_python_subpackage()
    for cr in reversed(missing):
        if cr.desired_vers:
            requires = "{} {}".format(cr.name, cr.desired_vers)
        else:
            requires = cr.name
        try:
            spec.add_python_requires(requires, main_py_subpkg)
            cr.autosync = "added"
            cr.vers = cr.desired_vers
            met.append(cr)
            missing.remove(cr)
        except exception.CouldNotAddPythonRequires as e:
            cr.autosync_error_msg = e.msg_fmt
    for cr in reversed(wrong_version):
        is_edited = spec.edit_python_requires_version_by_name(
            cr.name,
            cr.desired_vers)
        if is_edited:
            cr.autosync = "edited"
            cr.vers = cr.desired_vers
            met.append(cr)
            wrong_version.remove(cr)
        else:
            cr.autosync_error_msg = "Unabled to edit the module"
    for cr in reversed(removed):
        is_removed = spec.remove_python_requires_by_name(cr.name)
        if is_removed:
            cr.autosync = "removed"
            met.append(cr)
            removed.remove(cr)
        else:
            cr.autosync_error_msg = "Unabled to remove the module"
    spec.save()


def reqcheck_print(check=None, output=None, spec=False, strict=False):
    if output not in ['spec', 'json', 'text']:
        raise exception.WrongOutputFormat()
    if spec:
        output = 'spec'
    elif strict:
        _reqs.print_reqcheck(*check, format=output)
        # missing
        if len(check[3]) > 0:
            raise exception.ReqCheckMissingDependencies()
        # mismatch
        if len(check[2]) > 0:
            raise exception.ReqCheckMismatchingDependencies()
    else:
        _reqs.print_reqcheck(*check, format=output)


def reqquery(reqs_file=None, reqs_ref=None, spec=False, filter=None,
             dump=None, dump_file=None, load=None, load_file=None,
             verbose=False):
    if not (reqs_ref or reqs_file or spec or load or load_file):
        reqs_ref = guess.patches_base_ref()
    if not (bool(reqs_ref) ^ bool(reqs_file) ^ bool(spec)
            ^ bool(load) ^ bool(load_file)):
        raise exception.InvalidUsage(
            why="Only one requirements source (-r/-R/-s/-l/-L) can be "
                "selected.")
    if dump and dump_file:
        raise exception.InvalidUsage(
            why="Only one dump method (-d/-D) can be selected.")
    if dump:
        dump_file = 'requirements.yml'
    if load:
        load_file = 'requirements.yml'

    # get query results as requested
    if load_file:
        log.info("Loading query results from file: %s" % load_file)
        r = yaml.load(open(load_file))
    else:
        release, dist = None, None
        if not filter:
            try:
                release, dist = guess.osreleasedist()
                log.info('Autodetected filter: %s/%s'
                         % (release, dist))
            except exception.CantGuess as ex:
                raise exception.CantGuess(
                    msg='%s\n\nPlease select RELEASE(/DIST) filter to query.' %
                        str(ex))
        else:
            release, _, dist = filter.partition('/')
        module2pkg = True
        if reqs_file:
            log.info("Querying requirements file: %s" % reqs_file)
            reqs = _reqs.get_reqs_from_path(reqs_file)
        elif reqs_ref:
            log.info("Querying requirements file from git: "
                     "%s -- requirements.txt" % reqs_ref)
            reqs = _reqs.get_reqs_from_ref(reqs_ref)
        else:
            log.info("Querying .spec file")
            module2pkg = False
            reqs = _reqs.get_reqs_from_spec(as_objects=True)
        log.info('')
        r = _reqs.reqquery(reqs, release=release, dist=dist,
                           module2pkg=module2pkg, verbose=verbose)

    if dump_file:
        log.info("Saving query results to file: %s" % dump_file)
        yaml.dump(r, open(dump_file, 'w'))

    _reqs.print_reqquery(r)


def query(filter, package, verbose=False):
    r = _query.query_rdo(filter, package, verbose=verbose)
    if not r:
        log.warn('No distrepos information in distroinfo for %s' % filter)
        return
    if verbose:
        print('')
    _query.pretty_print_query_results(r)
