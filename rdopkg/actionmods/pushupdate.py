from collections import defaultdict
import os
import shutil
import tempfile
import yaml

import rdoupdate.core
import rdoupdate.exception

from rdopkg import const
from rdopkg import exception
from rdopkg import helpers
from rdopkg.utils import log
from rdopkg.utils.cmd import run, git


def _get_temp_dir():
    home = os.path.expanduser('~')
    return tempfile.mkdtemp(prefix='rdopkg.push', dir=home)


def copy_package(pkg_path, dest_dir, overwrite=False):
    helpers.ensure_dir(dest_dir)
    pkg_name = os.path.basename(pkg_path)
    dst_path = os.path.join(dest_dir, pkg_name)
    if not overwrite and os.path.exists(dst_path):
        raise exception.NewPackageAlreadyPresent(path=dst_path)
    log.info("{t.bold}copy{t.normal} {src} {t.bold}->{t.normal} {dst}".format(
        src=pkg_path, dst=dst_path, t=log.term))
    shutil.copyfile(pkg_path, dst_path)
    return dst_path


class UpdatePusher(object):
    def __init__(self, update_repo_path, dest_base, ready_dir='ready',
                 temp_path=None, sign_tool_path=None,
                 update_files=None, fails=None,
                 overwrite=False, debug=False):
        self.update_repo_path = update_repo_path
        self.dest_base = dest_base
        self.ready_dir = ready_dir or ''
        self.pushed_dir = 'pushed'
        self.pushed_files_ext = '.files'
        self.temp_path = temp_path
        self.update_files = update_files or []
        self.fails = fails or []
        self.overwrite = overwrite
        self.debug = debug
        self._sign_tool_path = sign_tool_path

    def _get_dir_path(self, directory):
        if not directory:
            return self.update_repo_path
        return os.path.join(self.update_repo_path, directory)

    def ready_path(self):
        return self._get_dir_path(self.ready_dir)

    def pushed_path(self):
        return self._get_dir_path(self.pushed_dir)

    def get_update_files(self):
        ready_path = self.ready_path()
        self.update_files = [os.path.join(self.ready_dir, f) for
                             f in os.listdir(ready_path)
                             if os.path.isfile(os.path.join(ready_path, f))]
        return self.update_files

    def _update_failed(self, update_file, error, stage):
        errs = str(error)
        self.fails.append((update_file, errs, stage))
        log.warn("Failed during %s for %s: %s" % (stage, update_file, errs))

    def _update_dir_path(self, update_file):
        return os.path.join(self.temp_path, update_file)

    def _update_file_path(self, update_file):
        return os.path.join(self.update_repo_path, update_file)

    def _load_update_file(self, update_file):
        upf_path = self._update_file_path(update_file)
        stream = file(upf_path, 'r')
        data = yaml.load(stream)
        try:
            update = rdoupdate.core.Update(data)
        except rdoupdate.exception.InvalidUpdateStructure as ex:
            msg = "%s: %s" % (update_file, str(ex))
            raise rdoupdate.exception.InvalidUpdateStructure(msg=msg)
        stream.close()
        return update

    def _build_tmp_path(self, update_file, build):
        upd_path = self._update_dir_path(update_file)
        return build.path(prefix=upd_path)

    def _dest_repo_base_path(self, repo):
        return self.dest_base + repo

    def _dest_repo_path(self, repo, dist):
        return os.path.join(self._dest_repo_base_path(repo), dist)

    def _build_dest_path(self, build):
        path = self._dest_repo_path(build.repo, build.dist)
        if build.tag:
            path = os.path.join(path, build.tag)
        return path

    def _run_on_each(self, fun, step):
        done = []
        for upf in self.update_files:
            if self.debug:
                fun(upf)
                done.append(upf)
            else:
                try:
                    fun(upf)
                    done.append(upf)
                except Exception as ex:
                    self._update_failed(upf, ex, step)
                    if self.debug:
                        raise
        self.update_files = done
        return done

    @property
    def sign_tool_path(self):
        if not self._sign_tool_path:
            path, _ = os.path.split(self.dest_base)
            base_path = path
            while len(path) > 1:
                tool_path = os.path.join(path, const.SIGN_TOOL)
                if os.path.isfile(tool_path):
                    self._sign_tool_path = tool_path
                    break
                path, _ = os.path.split(path)
            if not self._sign_tool_path:
                raise exception.ToolNotFound(tool=const.SIGN_TOOL,
                                             path=base_path)
        return self._sign_tool_path

    def init_env(self):
        # ensure sign tool is available
        _ = self.sign_tool_path
        if not self.temp_path:
            self.temp_path = _get_temp_dir()

        def _init_env(upf):
            update_dir_path = self._update_dir_path(upf)
            helpers.ensure_dir(update_dir_path)

        return self._run_on_each(_init_env, 'init env')

    def download_packages(self):
        def _download_pkg(upf):
            update = self._load_update_file(upf)
            update.download(out_dir=self.temp_path, prefix=upf)

        return self._run_on_each(_download_pkg, 'rpm download')

    def check_collision(self):
        def _check_collision(upf):
            update = self._load_update_file(upf)
            for build in update.builds:
                src_path = self._build_tmp_path(upf, build)
                build_rpms = helpers.find_files(src_path, ext='.rpm')
                dest_repo_base_path = self._dest_repo_base_path(build.repo)
                if not os.path.isdir(dest_repo_base_path):
                    raise exception.NotADirectory(path=dest_repo_base_path)
                if not self.overwrite:
                    dest_path = self._build_dest_path(build)
                    for rpm in build_rpms:
                        pkg_name = os.path.basename(rpm)
                        pkg_dst = os.path.join(dest_path, pkg_name)
                        if os.path.exists(pkg_dst):
                            raise exception.NewPackageAlreadyPresent(path=pkg_dst)

        return self._run_on_each(_check_collision, 'collision check')

    def sign_packages(self):
        repos = defaultdict(set)

        def _sign_pkg(upf):
            update = self._load_update_file(upf)
            for build in update.builds:
                build_path = self._build_tmp_path(upf, build)
                repos[build.repo].add(build_path)

        self._run_on_each(_sign_pkg, 'sign')

        for repo, build_paths in repos.items():
            key = "rdo-%s" % repo
            log.info("Signing with %s..." % log.term.bold(key))
            rpms = set()
            for path in build_paths:
                build_rpms = helpers.find_files(path, ext='.rpm')
                rpms = rpms.union(build_rpms)
            cmd = [self.sign_tool_path, key] + list(rpms)
            run(*cmd, direct=True)
        return self.update_files

    def push_packages(self):
        updated_repo_bases = set()
        updated_repos = set()

        def _push_pkg(upf):
            log.info("\nPushing update {t.bold}{upf}{t.normal}".format(
                t=log.term, upf=upf))
            update = self._load_update_file(upf)
            pushed_rpms = []
            try:
                _updated_repos = set()
                _updated_repo_bases = set()
                _pushed_build_tmp_paths = []
                for build in update.builds:
                    src_path = self._build_tmp_path(upf, build)
                    if src_path in _pushed_build_tmp_paths:
                        continue
                    build_rpms = helpers.find_files(src_path, ext='.rpm')
                    dest_repo_base_path = self._dest_repo_base_path(build.repo)
                    if not os.path.isdir(dest_repo_base_path):
                        raise exception.NotADirectory(path=dest_repo_base_path)
                    dest_path = self._build_dest_path(build)
                    for rpm in build_rpms:
                        pushed_path = copy_package(rpm, dest_path,
                                                   overwrite=self.overwrite)
                        pushed_rpms.append(pushed_path)
                    _pushed_build_tmp_paths.append(src_path)
                    _updated_repo_bases.add(dest_repo_base_path)
                    _updated_repos.add(self._dest_repo_path(build.repo,
                                                            build.dist))

                with helpers.cdir(self.update_repo_path):
                    helpers.ensure_dir(self.pushed_dir)
                    upf_base = os.path.basename(upf)
                    pushed_upf = os.path.join(self.pushed_dir, upf_base)
                    pushed_files_fn = pushed_upf + self.pushed_files_ext
                    git('mv', upf, pushed_upf)
                    pushed_files_f = open(pushed_files_fn, 'w')
                    pushed_files_f.writelines(
                        map(lambda x: "%s\n" % x, pushed_rpms))
                    pushed_files_f.close()
                    git('add', pushed_files_fn)
                    try:
                        git('commit', '-m',
                            "Push %s" % rdoupdate.core.pp_update(upf))
                    except Exception:
                        git('git', 'reset', '--hard')
                        raise
                updated_repos.update(_updated_repos)
                updated_repo_bases.update(_updated_repo_bases)
            except Exception as ex:
                if pushed_rpms:
                    log.warn("Final push failed for %s, cleaning copied "
                             "packages" % upf)
                    for rpm in pushed_rpms:
                        log.info("{t.warn}remove{t.normal} {rpm}".format(
                            t=log.term, rpm=rpm))
                        os.remove(rpm)
                raise

        self._run_on_each(_push_pkg, 'final push')

        if updated_repos:
            log.info("\nRunning {t.cmd}createrepo{t.normal} on updated repos"
                     .format(t=log.term))
            for repo in sorted(updated_repos):
                run('createrepo', repo, direct=True)

        return sorted(updated_repo_bases)

    def print_summary(self):
        n_good = len(self.update_files)
        n_bad = len(self.fails)
        n_all = n_good + n_bad
        if self.update_files:
            log.success("\n%d update(s) SUCCEEDED:" % n_good)
            fmt = '{t.bold}{upf}{t.normal}'
            l = map(lambda x: fmt.format(t=log.term, upf=x), self.update_files)
            helpers.print_list(l)
        if self.fails:
            log.error("\n%s update(s) FAILED:" % n_bad)
            fmt = ("{t.warn}{upf}{t.normal} failed during "
                   "{t.bold}{stage}{t.normal}: {err}")
            l = map(lambda x: fmt.format(t=log.term, upf=x[0], err=x[1],
                                         stage=x[2]), self.fails)
            helpers.print_list(l)
        print

    def clean_env(self):
        shutil.rmtree(self.temp_path)
