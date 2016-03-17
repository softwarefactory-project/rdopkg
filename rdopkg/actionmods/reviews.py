# -*- encoding: utf-8 -*-

import os
import shutil
import tempfile

import rdoupdate.actions

from rdopkg.conf import cfg
from rdopkg.utils import cmd
from rdopkg.utils import log
from rdopkg.gerrit import filters
from rdopkg.gerrit import reviews
from update import UpdateInfo


def get_review_update_info(review, gitdir):
    url = review['url']
    patch_set = review['currentPatchSet']
    ref = patch_set['ref']
    uploader = patch_set['uploader']
    apprs = patch_set.get('approvals', [])
    authors = ["%s <%s>" % (uploader['name'], uploader['email'])]
    cmd.git('fetch', cfg['RDO_UPDATE_REPO'], ref, log_cmd=False)
    cmd.git('checkout', 'FETCH_HEAD', log_cmd=False)
    upf = rdoupdate.actions.get_last_commit_update('.')
    update = rdoupdate.actions.check_file(upf)
    uinfo = UpdateInfo(
        upf,
        update,
        authors,
        gerrit_url=url,
        gerrit_apprs=apprs)
    return uinfo


def get_updates_info(verbose=False):
    gitdir = tempfile.mkdtemp(prefix='rdopkg-list-updates')
    uinfos = []
    prev_cwd = os.getcwd()
    os.chdir(gitdir)
    try:
        cmd.git('init', log_cmd=False)
        f_project = filters.OrFilter()
        f_project.add_items('project', 'rdo-update')

        f_other = filters.Items()
        f_other.add_items('is', 'open')

        query = reviews.Query(cfg['RDO_UPDATE_GERRIT_HOST'])
        for review in query.filter(f_project, f_other):
            try:
                url = review.get('url', '???')
                if verbose:
                    log.info("Processing update review: %s" % url)
                uinfo = get_review_update_info(review, gitdir)
                uinfos.append(uinfo)
            except Exception as ex:
                if verbose:
                    log.warn("Error processing update review: %s: %s",
                             type(ex).__name__, str(ex))
                pass
    finally:
        os.chdir(prev_cwd)
        shutil.rmtree(gitdir)
    return uinfos
