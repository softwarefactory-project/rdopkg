# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import contextlib
import os

from rdopkg import exception
from rdopkg.utils.cmd import run
from rdopkg.utils.cmd import ShellCommand
from rdopkg.utils.issues import search_bug_references


@contextlib.contextmanager
def git_branch(branch):
    if branch:
        old_branch = git.current_branch()
        git('checkout', branch)
        try:
            yield
        finally:
            git('checkout', old_branch)
    else:
        yield


@contextlib.contextmanager
def git_revision(gitrev):
    if gitrev:
        old_gitrev = git.current_commit()
        git.checkout(gitrev)
        try:
            yield
        finally:
            git.checkout(old_gitrev)
    else:
        yield


class Git(ShellCommand):
    command = "git"

    def __call__(self, *params, **kwargs):
        # allows us to run git in isolated mode, avoiding interaction with user
        # specific config, like ~/.git-templates/hooks (used for testing)
        if kwargs.get('isolated', False):
            env = kwargs.get('env', os.environ.copy())
            env['GIT_CONFIG_NOSYSTEM'] = '1'
            env['GIT_CONFIG_NOGLOBAL'] = '1'
            kwargs['env'] = env
        return run(self.command, *params, **kwargs)

    def create_branch_from_remote(self, branch, remote_branch=None):
        lbr = self.local_branches()
        if branch in lbr or remote_branch in lbr:
            return
        if remote_branch is None:
            for rbr in self.remote_branches():
                br = rbr[rbr.find('/') + 1:]
                if rbr == branch or br == branch:
                    remote_branch = rbr
        elif remote_branch not in self.remote_branches():
            raise Exception("Branch %s doesn't exist in remotes" %
                            remote_branch)
        self.create_branch(branch, remote_branch)

    def _parse_output(self, out):
        output = [l.strip() for l in out.split("\n") if l]
        return output

    def _parse_branch_output(self, out):
        output = [l for l in self._parse_output(out) if l.find('HEAD') < 0]
        return output

    def remote_branches(self, remote=""):
        res = self("branch", "-r", "--no-color")
        branches = self._parse_branch_output(res)
        branches = [b.replace("remotes/", "")
                    for b in branches if b.startswith(remote)]
        return branches

    def local_branches(self):
        res = self("branch")
        res = self._parse_branch_output(res)
        res = [b.replace("* ", "") for b in res]
        return res

    def current_branch(self):
        branch = self('rev-parse', '--abbrev-ref', 'HEAD', log_cmd=False)
        return branch

    def current_commit(self):
        commit = self('rev-parse', 'HEAD', log_cmd=False)
        return commit

    def current_commit_message(self):
        commit_msg = self('log', '-n1', '--pretty=%B', log_cmd=False)
        return commit_msg

    def ref_exists(self, ref):
        o = self('show-ref', '--verify', '--quiet', ref,
                 fatal=False, log_cmd=False, log_fail=False)
        return o.success

    def branch_exists(self, branch):
        return self.ref_exists('refs/heads/%s' % branch)

    def object_type(self, ref):
        o = self('cat-file', '-t', ref,
                 fatal=False, log_cmd=False, log_fail=False)
        if not o:
            return None
        return o

    def is_clean(self):
        o = self('status', '-uno', '--porcelain', log_cmd=False)
        if o:
            return False
        return True

    def remotes(self):
        res = self("remote", "show", log_cmd=False)
        return self._parse_branch_output(res)

    def remote_branch_split(self, branch, fatal=True):
        parts = branch.split('/')
        n_parts = len(parts)
        if n_parts >= 2:
            remotes = self.remotes()
            for n in range(1, n_parts):
                remote = '/'.join(parts[:n])
                if remote in remotes:
                    _branch = '/'.join(parts[n:])
                    return remote, _branch
        if fatal:
            raise exception.InvalidRemoteBranch(branch=branch)
        return None, branch

    def remote_of_local_branch(self, branch):
        try:
            o = self('for-each-ref', '--format=%(upstream:short)',
                     'refs/heads/%s' % branch, log_cmd=False, log_fail=False)
        except exception.CommandFailed:
            return None
        if not o:
            return None
        return o

    def delete_branch(self, branch):
        if self.branch_exists(branch):
            self('branch', '-D', branch)

    def create_branch(self, new_branch, branch):
        try:
            self('branch', '-f', new_branch, branch)
        except exception.CommandFailed:
            # this could only fail if we're on the branch
            self('reset', '--hard', branch)

    def squash_last(self, branch=None):
        if branch is not None:
            self('checkout', branch)
        self("reset", "--soft", "HEAD~")
        # on git < 1.7.9 --no-edit can be done by:
        # git commit -C HEAD --amend
        self("commit", "--amend", "--no-edit")

    def branch_needs_push(self, branch=None):
        if not branch:
            branch = self.current_branch()
        remote_branch = self.remote_of_local_branch(branch)
        h1 = self.get_latest_commit_hash(branch)
        h2 = self.get_latest_commit_hash(remote_branch)
        return h1 != h2

    def linearize(self, starting_point, branch=None):
        if branch is not None and self.current_branch() != branch:
            self('checkout', branch)
        self('rebase', starting_point)

    def rev_range(self, from_revision, to_revision=None):
        rng = from_revision + '..'
        if to_revision:
            rng += to_revision
        return rng

    def get_commits(self, from_revision, to_revision=None):
        rng = self.rev_range(from_revision, to_revision)
        log_out = self('log', '--format=%h %s', rng, log_cmd=False)
        commits = self._parse_output(log_out)
        return map(lambda x: tuple(x.split(' ', 1)), commits)

    def get_commit_subjects(self, from_revision, to_revision=None):
        rng = self.rev_range(from_revision, to_revision)
        log_out = self('log', '--format=%s', rng, log_cmd=False)
        return self._parse_output(log_out)

    def get_commit_hashes(self, from_revision, to_revision=None):
        rng = self.rev_range(from_revision, to_revision)
        log_out = self('log', '--format=%h', rng, log_cmd=False)
        return self._parse_output(log_out)

    def get_commit_bzs(self, from_revision, to_revision=None):
        """
        Return a list of tuples, one per commit. Each tuple is (sha1, subject,
        bz_list). bz_list is a (possibly zero-length) list of numbers.
        """
        rng = self.rev_range(from_revision, to_revision)
        GIT_COMMIT_FIELDS = ['id', 'subject', 'body']
        GIT_LOG_FORMAT = ['%h', '%s', '%b']
        GIT_LOG_FORMAT = '%x1f'.join(GIT_LOG_FORMAT) + '%x1e'
        log_out = self('log', '--format=%s' % GIT_LOG_FORMAT, rng,
                       log_cmd=False, fatal=False)
        if not log_out:
            return []

        log = log_out.strip('\n\x1e').split("\x1e")
        log = [row.strip('\n\t ').split("\x1f") for row in log]
        log = [dict(zip(GIT_COMMIT_FIELDS, row)) for row in log]
        result = []
        for commit in log:
            bzs = search_bug_references(commit['subject'])
            bzs.extend(search_bug_references(commit['body']))
            result.append((commit['id'], commit['subject'], bzs))
        return result

    def get_latest_commit_hash(self, ref=None):
        cmd = ['log', '-n', '1', '--format=%H']
        if ref:
            cmd.append(ref)
        out = self(*cmd, log_cmd=False, log_fail=False, fatal=False)
        return out

    def get_latest_tag(self, branch=None):
        cmd = ['describe', '--abbrev=0', '--tags']
        if branch:
            cmd.append(branch)
        out = self(*cmd, log_cmd=False)
        return out

    def get_file_authors(self, path, with_email=True):
        if with_email:
            pf = '%an <%ae>'
        else:
            pf = '%an'
        authors = self('log', '--oneline', "--pretty=%s" % pf, path,
                       log_cmd=False)
        authors = reversed(authors.split('\n'))
        return authors

    def get_file_content(self, rev, path):
        obj = '%s:%s' % (rev, path)
        return self('show', obj, log_cmd=False)

    def config_get(self, param, default=None):
        '''Return the value of a git configuration option.  This will
        return the value of the default parameter (which defaults to
        None) if the given option does not exist.'''

        try:
            return self("config", "--get", param,
                        log_fail=False, log_cmd=False)
        except exception.CommandFailed:
            return default

    def config_set(self, param, value, is_global=False):
        params = [param, value]
        if is_global:
            params.insert(0, '--global')
        return self("config", *params)

    def checkout(self, branch):
        self("checkout", branch, log_cmd=False)

    def remove(self, hash):
        self('rebase', '--onto', hash + '^', hash, '--preserve-merges',
             '--committer-date-is-author-date')


git = Git()
