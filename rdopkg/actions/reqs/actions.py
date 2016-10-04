"""
Requirements related actions.
"""
import os
import re
import yaml

from rdopkg import exception
from rdopkg import guess
from rdopkg.actionmods import query as _query
from rdopkg.actionmods import reqs as _reqs
from rdopkg.utils import log
from rdopkg.utils.cmd import git


def reqdiff(version_tag_from, version_tag_to):
    fmt = "\n{t.bold}requirements.txt diff{t.normal} between " \
          "{t.bold}{old}{t.normal} and {t.bold}{new}{t.normal}:"
    log.info(fmt.format(t=log.term, old=version_tag_from, new=version_tag_to))
    rdiff = _reqs.reqdiff_from_refs(version_tag_from, version_tag_to)
    _reqs.print_reqdiff(*rdiff)


def reqcheck(version):
    if version.upper() == 'XXX':
        if 'upstream' in git.remotes():
            current_branch = git.current_branch()
            branch = current_branch.replace('rpm-', '')
            if branch != 'master':
                branch = 'stable/{}'.format(branch)
            version = 'upstream/{}'.format(branch)
            check = _reqs.reqcheck_spec(ref=version)
        else:
            m = re.search(r'/([^/]+)_distro', os.getcwd())
            if not m:
                raise exception.CantGuess(what="requirements.txt location",
                                          why="failed to parse current path")
            path = '../%s/requirements.txt' % m.group(1)
            log.info("Delorean detected. Using %s" % path)
            check = _reqs.reqcheck_spec(reqs_txt=path)
    else:
        check = _reqs.reqcheck_spec(ref=version)
    _reqs.print_reqcheck(*check)


def reqquery(reqs_file=None, reqs_ref=None, spec=False, filter=None,
             dump=None, dump_file=None, load=None, load_file=None,
             verbose=False):
    if not (reqs_ref or reqs_file or spec or load or load_file):
        reqs_ref = guess.current_version()
    if not (bool(reqs_ref) ^ bool(reqs_file) ^ bool(spec) ^
            bool(load) ^ bool(load_file)):
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
        log.warn('No distrepos information in rdoinfo for %s' % filter)
        return
    if verbose:
        print('')
    _query.pretty_print_query_results(r)
