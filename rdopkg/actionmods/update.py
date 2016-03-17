# -*- encoding: utf-8 -*-

from collections import defaultdict
import glob
import os
import random
import shutil
import string

from rdopkg import exception
from rdopkg import guess
from rdopkg import helpers
from rdopkg import repoman
from rdopkg.utils import log
from rdopkg.utils import cmd

import rdoupdate.actions
import rdoupdate.core
import rdoupdate.exception


UPDIR_DESC = {
    '__reviews__': 'under review (being smoke-tested)',
    'updates': 'passed smoke test',
    'ready': 'ready for push'
}
UPFILE = 'up.yml'
FILLME = 'FILLME'


def generate_id(size=4, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def pretty_print_uinfos_dict(uinfos_dict):
    for upd in sorted(uinfos_dict, reverse=True):
        print('')
        uinfos = uinfos_dict[upd]
        title = '%d updates' % len(uinfos)
        if upd in UPDIR_DESC:
            title += " %s:" % UPDIR_DESC[upd]
        else:
            title += " in %s/" % upd
        print(log.term.bold_blue(title))
        for ui in uinfos:
            print('')
            ui.pretty_print()


def pretty_print_gerrit_approval(appr):
    val_str = appr['value']
    type_str = appr['type'][0]
    astr = "%s%s" % (val_str, type_str)
    try:
        val = int(val_str)
    except TypeError:
        val = 0
    if val > 0:
        astr = log.term.green(astr)
    elif val < 0:
        astr = log.term.red(astr)
    else:
        astr = log.term.bold(astr)
    return astr


def ensure_update_notes(upfile_path):
    update = None
    ok = False
    while not ok:
        update = rdoupdate.actions.check_file(upfile_path)
        if (not update.notes or update.notes == FILLME or
                update.notes == rdoupdate.core.FILL_THIS):
            fmt = ("\n{t.important}Please describe this update "
                   "in the 'notes' field.\n\n"
                   "Press <Enter> to edit update file: {upf}{t.normal}\n")
            raw_input(fmt.format(t=log.term, upf=upfile_path))
            helpers.edit(upfile_path)
        else:
            ok = True
    return update


def update_rdoinfo_check(update):
    fail_msg = None
    warn = False
    rls = defaultdict(set)
    for b in update.builds:
        rls[b.repo].add(b)
    log.info("Checking update using rdoinfo...".format(
        t=log.term))
    for r, builds in rls.items():
        rbuilds = guess.builds(r)
        rbuilds_ = list(rbuilds)
        if not rbuilds:
            msg = 'Unknown OpenStack release: %s' % r
            log.warn(msg)
            if not fail_msg:
                fail_msg = msg
            continue
        for b in builds:
            found = False
            for dist_, src_ in rbuilds:
                if b.dist == dist_:
                    found = True
                    rbuilds_ = filter(lambda x: x[0] != b.dist, rbuilds_)
                    break
            if not found:
                msg = 'Unexpected %s build: %s' % (r, b.dist)
                log.warn(msg)
                if not fail_msg:
                    fail_msg = msg
        for dist_, src_ in rbuilds_:
            log.info('Missing %s build: %s' % (r, dist_))
            warn = True
    if fail_msg:
        raise exception.UpdateCheckFailed(fail=fail_msg)
    if warn:
        helpers.confirm("Submit anyway?")


def update_summary(update):
    u = defaultdict(set)
    for build in update.builds:
        u[build.repo].add(build.dist)
    s = ''
    for rls in sorted(u.keys()):
        if s:
            s += '/'
        s += rls
        for dist in u[rls]:
            s += '_' + dist
    return s


class UpdateInfo(object):

    def __init__(self, upf, update, authors,
                 gerrit_url=None, gerrit_apprs=None):
        self.upf = upf
        self.update = update
        self.authors = authors
        self.gerrit_url = gerrit_url
        self.gerrit_apprs = gerrit_apprs

    def pretty_print(self):
        fmt = '{t.bold}{upf}{t.normal} by {t.bold}{authors}{t.normal}'
        print(fmt.format(t=log.term, upf=self.upf,
                         authors=', '.join(self.authors)))
        if self.gerrit_url:
            fmt = "{t.bold}gerrit URL:{t.normal} {url}"
            print(fmt.format(t=log.term, url=self.gerrit_url))
        if self.gerrit_apprs is not None:
            if self.gerrit_apprs:
                apprs = ", ".join(map(pretty_print_gerrit_approval,
                                      self.gerrit_apprs))
            else:
                apprs = log.term.yellow('none')
            fmt = "{t.bold}gerrit approvals:{t.normal} {apprs}"
            print(fmt.format(t=log.term, apprs=apprs))
        print(str(self.update))


class UpdateRepo(repoman.RepoManager):
    repo_desc = 'update'
    updates_path = 'updates'

    def _upfile_path(self, id):
        return os.path.join(self.updates_path, "%s.yml" % id)

    def _upfile_path_abs(self, id):
        return os.path.join(self.repo_path, self._upfile_path(id))

    def submit_update_file(self, id, msg=''):
        upfile_path = self._upfile_path(id)
        with self.repo_dir():
            if not os.path.isfile(upfile_path):
                raise exception.UpdateFileNotFound(path=upfile_path)
            update = rdoupdate.actions.check_file(upfile_path)
            branch = update_summary(update)
            commit_msg = "New %s" % id
            if msg:
                commit_msg += "\n\n%s\n" % msg
            log.info("Setting up gerrit.")
            cmd.git('review', '-s', direct=True)
            cmd.git('branch', branch, 'origin/master')
            try:
                cmd.git('checkout', '-f', branch)
                cmd.git('add', upfile_path)
                cmd.git('commit', '-F', '-', input=commit_msg)
                log.info("Submitting update for review.")
                cmd.git('review', direct=True)
            finally:
                pass
                cmd.git('checkout', '-f', 'master')
                cmd.git('branch', '-D', branch)

    def _get_new_update_id(self):
        looking = True
        while looking:
            update_id = generate_id()
            upfile_path = self._upfile_path_abs(update_id)
            if os.path.exists(upfile_path):
                log.info("Generated colliding ID %s. Weird. "
                         "Generating new ID.")
            else:
                looking = False
        return update_id, upfile_path

    def submit_existing_update(self, upfile_path, check_availability=True):
        update = ensure_update_notes(upfile_path)
        update_rdoinfo_check(update)
        if check_availability:
            log.info("Checking availability of updated builds...")
            for b in update.builds:
                r = b.is_available(verbose=True)
                if not r:
                    raise rdoupdate.exception.BuildNotAvailable(
                        build_id=b.id, source=b.source, detail=r.err)
        update_id, tmp_upfile_path = self._get_new_update_id()
        tmp_updir_path, _ = os.path.split(tmp_upfile_path)
        helpers.ensure_dir(tmp_updir_path)
        shutil.copyfile(upfile_path, tmp_upfile_path)
        print("\nUpdate:\n%s\n" % update)
        self.submit_update_file(update_id, msg=str(update))

    # XXX: Unused, unmaintained.
    def new_update(self, update, check_availability=True):
        update_id, upfile_path = self._get_new_update_id()
        updir_path, _ = os.path.split(upfile_path)
        helpers.ensure_dir(updir_path)
        upfile = file(upfile_path, 'wt')
        upfile.write(update.update_file())
        upfile.close()
        helpers.edit(upfile_path)
        cmd.run('/bin/sed', '-i', '-e', '/^#/d', upfile_path, shell=False)
        parsed_update = None
        while not parsed_update:
            try:
                parsed_update = rdoupdate.actions.check_file(upfile_path)
            except Exception as ex:
                print("\n{t.important}Error parsing update file: {t.normal}"
                      "{t.warn}{ex}{t.normal}".format(t=log.term, ex=ex))
                again = raw_input("Do you want to edit? [Yn] ")
                if again and again.lower() != 'y':
                    os.remove(upfile_path)
                    raise exception.UserAbort()
                helpers.edit(upfile_path)
                continue
            if check_availability:
                log.info("Checking availability of updated builds...")
                bad_builds = [x for x in parsed_update.builds
                              if not x.is_available(verbose=True)]
                if bad_builds:
                    builds_str = "\n".join(map(str, bad_builds))
                    print("\n{t.important}Builds below doesn't seem to be "
                          "available:{t.normal}\n{builds}\n".format(
                              t=log.term, builds=builds_str))
                    print("Options:")
                    print("  e: Edit update")
                    print("  u: Update anyway")
                    print("  a: Abort")
                    resp = raw_input("What do you want to do? [euA] ").lower()
                    if resp == 'e':
                        parsed_update = None
                        helpers.edit(upfile_path)
                    elif resp == 'u':
                        pass
                    else:
                        raise exception.UserAbort()
        print("\nUpdate:\n%s\n" % parsed_update)
        self.submit_update_file(update_id, msg=str(parsed_update))

    def get_updates_info_by_dir(self):
        updates = defaultdict(list)
        with self.repo_dir():
            for upf_path in glob.glob('*/*.yml'):
                upd, upf = os.path.split(upf_path)
                if upd in ('pushed', 'rollback'):
                    continue
                try:
                    update = rdoupdate.actions.check_file(upf_path)
                except Exception as ex:
                    continue

                authors = cmd.git.get_file_authors(upf_path)
                uinfo = UpdateInfo(upf_path, update, authors)
                updates[upd].append(uinfo)
        return updates

    def pretty_print_updates(self):
        uinfos_dict = self.get_updates_info_by_dir()
        pretty_print_uinfos_dict(uinfos_dict)


def dump_build(build, update_file):
    if os.path.isfile(update_file):
        update = rdoupdate.actions.check_file(update_file)
        found = False
        for b in update.builds:
            if b.__dict__ == build.__dict__:
                found = True
                break
        if found:
            log.info(
                "\nBuild already present in update file: %s" %
                update_file)
        else:
            log.info("\nAppending build to update file: %s" % update_file)
            update.builds.append(build)
    else:
        log.info("\nSaving build to new update file: %s" % update_file)
        update = rdoupdate.core.Update(builds=[build],
                                       notes=FILLME)
    helpers.ensure_new_file_dirs(update_file)
    file(update_file, 'w').write(update.update_file(hints=False))
