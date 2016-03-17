# -*- encoding: utf-8 -*-

import ConfigParser
import datetime
from functools import wraps
import json
import os
import re
import requests
import time

from rdopkg import exception
from rdopkg.utils import cmd
from rdopkg.utils import log


COPR_URL = 'https://copr.fedoraproject.org'
COPR_RESULTS_URL = 'http://copr-be.cloud.fedoraproject.org/results'


def fpo_url(pkg, user):
    return "http://%s.fedorapeople.org/copr/%s" % (user, pkg)


def upload_fpo(pkg, user):
    dst_host = user + '@fedorapeople.org'
    dst_path = '~/public_html/copr'
    dst = '%s:%s/%s' % (dst_host, dst_path, pkg)
    _cmd = ['scp', pkg, dst]
    url = fpo_url(pkg, user)
    try:
        cmd.run(*_cmd)
    except exception.CommandFailed as ex:
        err = ex.kwargs['out'].stderr
        # TODO: fragile, use paramiko instead?
        if not re.match('scp: .*No such file or directory', err):
            raise
        log.info("Creating remote dir: %s:%s" % (dst_host, dst_path))
        cmd.run('ssh', dst_host, 'mkdir -p ' + dst_path)
        cmd.run(*_cmd)
    return url


def rdo_copr_name(release, dist):
    return 'rdo-%s-%s' % (release, dist)


def copr_fetcher_id(srpm_url):
    _, _, srpm = srpm_url.rpartition('/')
    if srpm.endswith('.src.rpm'):
        srpm = srpm[:-8]
    return srpm


def _get_copr_data(req, user, type=None):
    if '<title>Sign in Coprs</title>' in req.text:
        raise exception.CoprError(code=403, error='Invalid API token')
    if req.status_code == 404:
        raise exception.CoprError(
            code=req.status_code,
            error="404 for user %s" %
            user.get('username'))
    try:
        output = json.loads(req.text)
    except ValueError:
        raise exception.CoprError(
            code=req.status_code,
            error="Invalid response (not JSON):\n%s" %
            req.text)
    if req.status_code != 200:
        msg = "[%s] %s" % (req.status_code, output['error'])
        if (type == 'new_build' and
                    req.status_code == 500 and
                    output.get('error') == 'Invalid request'):
            msg += ("\nThis funny copr response might mean you don't have "
                    "permission to build in this copr. Or not. Hahaha.")
        raise exception.CoprError(code=req.status_code,
                                  copr_msg=output.get('error'),
                                  error=msg)
    return output


def get_copr_conf_fn():
    return os.path.join(os.path.expanduser('~'), '.config', 'copr')


def get_copr_user():
    config = ConfigParser.ConfigParser()
    config_fn = get_copr_conf_fn()
    if not config.read(config_fn):
        raise exception.CoprError(
            error="Configuration file %s not found.\n"
                  "See `man copr-cli` for more information" % config_fn)
    try:
        username = config.get('copr-cli', 'username', None)
        login = config.get('copr-cli', 'login', None)
        token = config.get('copr-cli', 'token', None)
    except ConfigParser.Error as err:
        raise exception.CoprError(
            'Bad configuration file %s: %s' % (config_fn, err))
    return {'username': username, 'token': token, 'login': login}


def get_copr_url():
    config = ConfigParser.ConfigParser()
    config.read(get_copr_conf_fn())
    copr_url = COPR_URL
    if (config.has_section('copr-cli') and
            config.has_option('copr-cli', 'copr_url')):
        copr_url = config.get('copr-cli', 'copr_url')
    return copr_url


def need_user(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        obj = args[0]
        if not obj.user:
            obj.user = get_copr_user()
        return f(*args, **kwargs)
    return wrapper


class RdoCoprs(object):

    def __init__(self, owner='jruzicka', copr_url=None, copr_results_url=None):
        self.owner = owner
        self.user = {}
        self.copr_url = copr_url or get_copr_url()
        self.copr_results_url = copr_results_url or COPR_RESULTS_URL

    def copr_api_url(self, path):
        return "%s/api/%s" % (self.copr_url, path)

    def get_builds_url(self, release, dist):
        copr = rdo_copr_name(release, dist)
        return '{0}/coprs/{1}/{2}/builds'.format(
            self.copr_url, self.owner, copr)

    def get_repo_url(self, release, dist):
        copr = rdo_copr_name(release, dist)
        return '{0}/{1}/{2}/{3}-x86_64'.format(
            self.copr_results_url, self.owner, copr, dist)

    @need_user
    def _fetch_build_status(self, build_id):
        url = self.copr_api_url('coprs/build_status/%s/' % build_id)
        req = requests.get(url, auth=(self.user['login'], self.user['token']))
        output = _get_copr_data(req, self.user)
        if 'status' in output:
            return output['status']
        if 'error' in output:
            raise exception.CoprError(error=output['error'])
        raise exception.CoprError(
            error="Build status query returned no results.")

    @need_user
    def new_build(self, srpm_url, release, dist, watch=False):
        copr = rdo_copr_name(release, dist)
        url = self.copr_api_url('coprs/%s/%s/new_build/' % (self.owner, copr))
        data = {
            'pkgs': srpm_url,
        }

        req = requests.post(url,
                            auth=(self.user['login'], self.user['token']),
                            data=data)
        output = _get_copr_data(req, self.user, type='new_build')
        build_ids = output.get('ids')
        if not build_ids:
            raise exception.CoprError(
                error="copr didn't return id of new build.(?!)")
        build_id = build_ids[0]
        if watch:
            log.info("\nWatching build (may be safely interrupted)...")
            prevstatus = None
            try:
                while True:
                    try:
                        status = self._fetch_build_status(build_id)
                    except exception.CoprError as ex:
                        log.warn("Failed to get build status: %s" % ex)
                        break

                    if prevstatus != status:
                        now = datetime.datetime.now()
                        if status in ['pending', 'waiting', 'running']:
                            cstatus = log.term.bold(status)
                        elif status == 'succeeded':
                            cstatus = log.term.good(status)
                        elif status == 'failed':
                            cstatus = log.term.error(status)
                        elif status == 'skipped':
                            cstatus = ("{t.magenta}{st}{t.normal} (build "
                                       "already done)".format(t=log.term,
                                                              st=status))
                        else:
                            cstatus = log.term.warn(status)
                        log.info("[%s] %s" % (now.strftime('%H:%M:%S'),
                                              cstatus))
                        prevstatus = status

                    if status in [
                            'succeeded',
                            'failed',
                            'canceled',
                            'skipped']:
                        break

                    time.sleep(60)
            except KeyboardInterrupt:
                pass
            except Exception as ex:
                log.warn("Error during copr build monitoring: %s" % ex)

        return build_id

    @need_user
    def ensure_cli_setup(self):
        # sadly, I found no better way, copr API sux
        try:
            build_id = self.new_build('X', 'icehouse', 'epel-7')
        except exception.CoprError as ex:
            code = ex.kwargs.get('code')
            if code != 500 or ex.kwargs.get('copr_msg') != 'Invalid request':
                raise
