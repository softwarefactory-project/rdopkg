import os
import re
import shutil
import time

from rdopkg import exception
from rdopkg.conf import cfg
from rdopkg.utils import log
from rdopkg.utils import cmd
from rdopkg import helpers


def repo_name_from_url(repo_url):
    if repo_url:
        i = repo_url.rfind('/')
        if i != -1:
            d = repo_url[i+1:]
            if d.endswith('.git'):
                d = d[:-4]
            return d
    return None


class RepoManager(object):
    repo_desc = 'git'

    def __init__(self, base_path=None, url=None, local_repo_path=None,
                 verbose=False):
        # remote repo (base_path, url) XOR local repo (local_repo_path)
        assert bool(base_path and url) != bool(local_repo_path)

        self.url = url
        self.verbose = verbose
        if local_repo_path:
            self.repo_path = local_repo_path
            self.base_path, self.repo_name = \
                os.path.split(os.path.abspath(local_repo_path))
        else:
            self.base_path = base_path
            self.repo_name = repo_name_from_url(self.url)
            if not self.repo_name:
                raise exception.RepoError(
                    what='Failed to parse %s repo URL: %s' % (self.repo_desc,
                                                              self.url))
            self.repo_path = os.path.join(self.base_path, self.repo_name)

    def _nuke(self):
        log.info("Removing %s repo: %s" % (self.repo_desc, self.repo_path))
        shutil.rmtree(self.repo_path, ignore_errors=True)

    def _clone(self):
        if self.verbose:

            log.info("Cloning {desc} repo: {url}\n"
                     "        {space} into: {path}".format(
                desc=self.repo_desc,
                space=len(self.repo_desc) * ' ',
                url=self.url,
                path=self.repo_path))
        with helpers.cdir(self.base_path):
            cmd.git('clone', self.url, self.repo_name, log_cmd=self.verbose)

    def _fetch(self, force=False):
        need_fetch = True
        with self.repo_dir():
            if not force:
                try:
                    t_fetch = os.path.getmtime('.git/FETCH_HEAD')
                    t_now = int(time.time())
                    delta = t_now - t_fetch
                    if delta < cfg['FETCH_PERIOD']:
                        need_fetch = False
                except Exception:
                    pass
            if need_fetch:
                if self.verbose:
                    log.info("Fetching %s repo: %s" % (
                        self.repo_desc, self.repo_path))
                cmd.git('fetch', 'origin', log_cmd=self.verbose)
                cmd.git('checkout', '-f', 'master', log_cmd=self.verbose)
                cmd.git('reset', '--hard', 'origin/master',
                        log_cmd=self.verbose)

    def repo_dir(self):
        return helpers.cdir(self.repo_path)

    def git_check_remote(self):
        assert(self.url)
        with self.repo_dir():
            remotes = cmd.git('remote', '-v', log_cmd=False)
        pattern = '^origin\s+%s\s+\(fetch\)$' % re.escape(self.url)
        if not re.search(pattern, remotes, re.MULTILINE):
            raise exception.RepoError(what="origin isn't set to expected URL: "
                                           "%s" % self.url)

    def init(self, force_fetch=False):
        if not self.url:
            if not os.path.isdir(self.repo_path):
                raise exception.NotADirectory(path=self.repo_path)
            return
        if self.base_path and not os.path.isdir(self.base_path):
            if self.verbose:
                log.info("Creating base directory: %s" % self.base_path)
            os.makedirs(self.base_path)
        if not os.path.isdir(self.repo_path):
            self._clone()
        else:
            try:
                self.git_check_remote()
            except exception.RepoError as e:
                if self.verbose:
                    log.warn("%s repo didn't pass the checks, renewing: %s"
                             % (self.repo_desc, e))
                self._nuke()
                self._clone()
            else:
                self._fetch(force=force_fetch)
