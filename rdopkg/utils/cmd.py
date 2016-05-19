import subprocess

import exception
import json
import log
import re


class _CommandOutput(str):
    """
    Just a string subclass with attribute access.
    """
    @property
    def success(self):
        return self.return_code == 0


def log_cmd_fail(cmd, cout, fail_log_fun=log.warn, out_log_fun=log.info):
    fail_log_fun('{t.error}command failed: {t.normal}{t.cmd}{cmd}{t.normal}'
                 .format(t=log.term, cmd=cmd))
    nl = False
    if cout:
        out_log_fun(log.term.bold("stdout:"))
        out_log_fun(cout)
        nl = True
    if cout.stderr:
        out_log_fun(log.term.bold("stderr:"))
        out_log_fun(cout.stderr)
        nl = True
    if nl:
        out_log_fun('')


def run(cmd, *params, **kwargs):
    fatal = kwargs.get('fatal', True)
    direct = kwargs.get('direct', False)
    log_cmd = kwargs.get('log_cmd', True)
    log_fail = kwargs.get('log_fail', True)
    input = kwargs.get('input')
    print_stdout = kwargs.get('print_stdout', False)
    print_stderr = kwargs.get('print_stderr', False)
    print_output = kwargs.get('print_output', False)

    cmd = [cmd] + list(params)
    cmd_str = ' '.join(cmd)

    if log_cmd:
        log.command(log.term.cmd(cmd_str))

    if print_output:
        print_stdout = True
        print_stderr = True

    if input:
        stdin = subprocess.PIPE
    else:
        stdin = None

    if direct:
        stdout = None
        stderr = None
    else:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE

    try:
        prc = subprocess.Popen(cmd, stdin=stdin, stdout=stdout,
                               stderr=stdout)
    except OSError as ex:
        raise exception.CommandNotFound(cmd=cmd[0])
    out, err = prc.communicate(input=input)

    if out:
        out = out.rstrip()
        if print_stdout:
            log.info(out)
    else:
        out = ''

    if err:
        err = err.rstrip()
        if print_stderr:
            log.info(err)
    else:
        err = ''

    cout = _CommandOutput(out)
    cout.stderr = err
    cout.return_code = prc.returncode
    cout.cmd = cmd_str
    if prc.returncode != 0:
        if log_fail:
            log_cmd_fail(cmd_str, cout)
        if fatal:
            raise exception.CommandFailed(cmd=cmd, out=cout)
    return cout


class ShellCommand(object):
    command = None

    def __init__(self):
        if self.command is None:
            self.command = self.__class__.__name__.lower()

    def __call__(self, *params, **kwargs):
        return run(self.command, *params, **kwargs)


class Git(ShellCommand):
    command = "git"

    def create_branch_from_remote(self, branch, remote_branch=None):
        lbr = self.local_branches()
        if branch in lbr or remote_branch in lbr:
            return
        if remote_branch is None:
            for rbr in self.remote_branches():
                br = rbr[rbr.find('/')+1:]
                if rbr == branch or br == branch:
                    remote_branch = rbr
        elif remote_branch not in self.remote_branches():
            raise Exception("Branch %s doesnt exist in remotes" %
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

    def ref_exists(self, ref):
        o = self('show-ref', '--verify', '--quiet', ref,
                 fatal=False, log_cmd=False, log_fail=False)
        return o.success

    def branch_exists(self, branch):
        return self.ref_exists('refs/heads/%s' % branch)

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
        remote, sep, _ = o.partition('/')
        if not sep:
            return None
        return remote

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
                       log_cmd=False)
        log = log_out.strip('\n\x1e').split("\x1e")
        log = [row.strip().split("\x1f") for row in log]
        log = [dict(zip(GIT_COMMIT_FIELDS, row)) for row in log]
        BZ_REGEX = r'rhbz#(\d+)'
        result = []
        for commit in log:
            bzs = re.findall(BZ_REGEX, commit['subject'])
            bzs.extend(re.findall(BZ_REGEX, commit['body']))
            result.append((commit['id'], commit['subject'], bzs))
        return result

    def get_latest_commit_hash(self, ref=None):
        cmd = ['log', '-n', '1', '--format=%H']
        if ref:
            cmd.append(ref)
        out = self(*cmd, log_cmd=False)
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

    def config_get(self, param):
        return self("config", "--get", param)

    def config_set(self, param, value, is_global=False):
        params = [param, value]
        if is_global:
            params.insert(0, '--global')
        return self("config", *params)

    def checkout(self, branch):
        self("checkout", branch)

    def remove(self, hash):
        self('rebase', '--onto', hash+'^', hash, '--preserve-merges',
             '--committer-date-is-author-date')


class GerritQuery(ShellCommand):
        def __init__(self, host, port, log_cmd=True):
            self.host = host
            self.port = port
            self.log_cmd = log_cmd

        def __call__(self, *params, **kwargs):
            if 'log_cmd' not in kwargs:
                kwargs['log_cmd'] = self.log_cmd
            results = run('ssh', '-p', self.port, self.host,
                          'gerrit', 'query', '--format=JSON',
                          *params, **kwargs)
            # gerrit sends stats that we need to discard
            result = results.split('}\n{')[0]
            try:
                j = json.loads(result + '}')
            except ValueError:
                j = json.loads(result)
            if j.get('type') in ['error', 'stats']:
                # we have no results, just the query stats
                return None
            else:
                return j


git = Git()
