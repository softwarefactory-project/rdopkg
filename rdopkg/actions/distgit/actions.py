"""
This is the main rdopkg action module with actions for distgit management.
"""

import itertools
import os
import re
import sys
import yaml

from rdopkg. action import Action, Arg
from rdopkg.conf import cfg, cfg_files
from rdopkg import exception
from rdopkg import guess
from rdopkg.actionmods import rdoinfo
from rdopkg.actionmods import rpmfactory
from rdopkg.actionmods import reqs as _reqs
from rdopkg.utils import log
from rdopkg.utils.cmd import run, git
from rdopkg.utils import specfile
from rdopkg.utils import tidy_ssh_user
from rdopkg import helpers


FEDPKG = ['fedpkg']


def get_package_env(version=None, release=None, dist=None, branch=None,
                    patches_branch=None, local_patches_branch=None,
                    patches_style=None, gerrit_patches_chain=None):
    if not branch:
        branch = git.current_branch()
    if branch.endswith('-patches'):
        branch = branch[:-8]
        if git.branch_exists(branch):
            log.info(
                "This looks like -patches branch. Assuming distgit branch: "
                "%s" % branch)
            git.checkout(branch)
        else:
            raise exception.InvalidUsage(
                why="This action must be run on a distgit branch.")
    args = {
        'package': guess.package(),
        'branch': branch,
    }
    if not release or not dist:
        _release, _dist = guess.osreleasedist(branch, default=(None, None))
        if not release and _release:
            args['release'] = _release
        if not dist and _dist:
            args['dist'] = _dist
    osdist = guess.osdist()
    if osdist == 'RHOS':
        log.info("RHOS package detected.")
        args['fedpkg'] = ['rhpkg']
    if not patches_branch:
        patches_branch = guess.patches_branch(branch, pkg=args['package'],
                                              osdist=osdist)
    if not patches_style:
        patches_style = guess.patches_style(gerrit_patches_chain)
    args['patches_style'] = patches_style
    args['patches_branch'] = patches_branch
    if not local_patches_branch:
        args['local_patches_branch'] = patches_branch.partition('/')[2]
    if not version:
        version = guess.current_version()
        args['version'] = version
    args['version_tag_style'] = guess.version_tag_style(version=version)

    return args


def show_package_env(package, version,
                     branch, patches_branch, local_patches_branch,
                     release=None, dist=None, version_tag_style=None,
                     patches_style=None, gerrit_patches_chain=None):
    def _putv(title, val):
        print("{t.bold}{title}{t.normal} {val}"
              .format(title=title, val=val, t=log.term))

    osdist = guess.osdist()

    upstream_branch = guess.upstream_branch()
    if not git.ref_exists('refs/remotes/%s' % upstream_branch):
        upstream_version = 'upstream remote/branch not found'
    else:
        upstream_version = guess.upstream_version(branch=upstream_branch)
        if not upstream_version:
            upstream_version = 'no version tag found'

    if patches_style == 'review':
        if not gerrit_patches_chain:
            gerrit_patches_chain = guess.gerrit_patches_chain(verbose=False)
        gerrit_review_url = rpmfactory.review_url(gerrit_patches_chain) or \
            'unknown'

    nvr = specfile.Spec().get_nvr()
    print
    _putv('Package:  ', package)
    _putv('NVR:      ', nvr)
    _putv('Version:  ', version)
    _putv('Upstream: ', upstream_version)
    _putv('Tag style:', version_tag_style or 'X.Y.Z')
    print
    _putv('Patches style:         ', patches_style)
    _putv('Dist-git branch:       ', branch)
    _putv('Local patches branch:  ', local_patches_branch)
    _putv('Remote patches branch: ', patches_branch)
    _putv('Remote upstream branch:', upstream_branch or 'not found')
    if patches_style == 'review':
        _putv('Patches chain:         ', gerrit_review_url)
    print
    _putv('OS dist:               ', osdist)
    if osdist == 'RDO':
        rlsdist = '%s/%s' % (release or 'unknown', dist or 'unknown')
        _putv('RDO release/dist guess:', rlsdist)
        print


def _print_patch_log(patches, tag, n_excluded):
    n_patches = len(patches)
    print("\n{t.bold}{n} patches{t.normal} on top of {t.bold}{tag}{t.normal}"
          ", {t.bold}{ne}{t.normal} excluded\n".format(
              t=log.term, n=n_patches, tag=tag, ne=n_excluded))
    if n_patches <= 0:
        return
    ei = n_patches - n_excluded
    for hsh, title, bzs in patches:
        if ei > 0:
            chsh = log.term.green(hsh)
        else:
            chsh = log.term.red(hsh)
        bzlog = ' '.join(map(lambda x: 'rhbz#%s' % x, bzs))
        patchlog = "%s  %s" % (chsh, title)
        if bzlog != '':
            patchlog += ' (%s)' % bzlog
        print(patchlog)
        ei -= 1


def show_patch_log(version, patches_branch, version_tag_style=None):
    tag = guess.version2tag(version, version_tag_style)
    patches = git.get_commit_bzs(tag, patches_branch)
    spec = specfile.Spec()
    n_excluded = spec.get_n_excluded_patches()
    print("\nPatches branch {t.bold}{pb}{t.normal} is at version {t.bold}"
          "{ver}{t.normal}".format(
              t=log.term, pb=patches_branch, ver=version))
    _print_patch_log(patches, tag, n_excluded)


def conf():
    if cfg_files:
        log.info("Following config files were read:")
        helpers.print_list(cfg_files)
    else:
        log.info("No rdopkg config files found, using default config:")
    log.info("")
    for item in cfg.items():
        log.info("%s: %s" % item)


def new_version_setup(patches_branch=None, local_patches=False,
                      version=None, new_version=None, version_tag_style=None,
                      new_sources=None, no_new_sources=None):
    args = {}
    if new_version:
        # support both version and tag
        ver, _ = guess.tag2version(new_version)
        if ver != new_version:
            new_version = ver
            args['new_version'] = new_version
        new_version_tag = guess.version2tag(new_version, version_tag_style)
    else:
        ub = guess.upstream_branch()
        if not git.ref_exists('refs/remotes/%s' % ub):
            msg = ("Upstream branch not found: %s\n"
                   "Can't guess latest version.\n\n"
                   "a) provide new version (git tag) yourself\n"
                   "   $ rdopkg new-version 1.2.3\n\n"
                   "b) add upstream git remote:\n"
                   "   $ git remote add -f upstream GIT_URL\n"
                   % ub)
            raise exception.CantGuess(msg=msg)
        new_version_tag = git.get_latest_tag(ub)
        new_version, _ = guess.tag2version(new_version_tag)
        args['new_version'] = new_version
        log.info("Latest version detected from %s: %s" % (ub, new_version))
    if version == new_version:
        helpers.confirm(
            msg="It seems the package is already at version %s\n\n"
                "Run new-version anyway?" % version,
            default_yes=False)
    args['changes'] = ['Update to %s' % new_version]
    args['new_patches_base'] = new_version_tag
    spec = specfile.Spec()
    rpm_version = spec.get_tag('Version')
    rpm_milestone = spec.get_milestone()
    new_rpm_version, new_milestone = specfile.version_parts(new_version)
    args['new_rpm_version'] = new_rpm_version
    if new_milestone:
        args['new_milestone'] = new_milestone
    if (rpm_version != new_rpm_version or
            bool(new_milestone) != bool(rpm_milestone)):
        if new_milestone:
            args['new_release'] = '0.1'
        else:
            args['new_release'] = '1'
    if not local_patches:
        if not patches_branch or \
           not git.ref_exists('refs/remotes/' + patches_branch):
            log.warn("Patches branch '%s' not found. Running in --bump-only "
                     "mode." % patches_branch)
            args['bump_only'] = True
    if new_sources or no_new_sources:
        if new_sources and no_new_sources:
            raise exception.InvalidUsage(
                msg="DOES NOT COMPUTE: both -n and -N don't make sense.")
        # new_sources == not no_new_sources
    else:
        new_sources = guess.new_sources()
    args['new_sources'] = new_sources

    return args


def ensure_patches_branch(patches_branch=None, local_patches=False,
                          bump_only=False, patches_style=None):
    if local_patches or bump_only:
        return
    if not patches_branch:
        raise exception.CantGuess(
            what='remote patches branch',
            why="Specify with --patches-branch or use --local-patches")
    if not git.ref_exists('refs/remotes/%s' % patches_branch):
        raise exception.ConfigError(
            what=("remote patches branch '%s' not found. \n\n"
                  "Specify with -p/--patches-branch, use -l/--local-patches, "
                  "or skip patches branch operations with -b/--bump-only" %
                  patches_branch))


def clone(
        package,
        force_fetch=False,
        use_master_distgit=False,
        gerrit_remotes=False,
        review_user=None):
    inforepo = rdoinfo.get_default_inforepo()
    inforepo.init(force_fetch=force_fetch)
    pkg = inforepo.get_package(package)
    if not pkg:
        raise exception.InvalidRDOPackage(package=package)
    if use_master_distgit:
        try:
            distgit = pkg['master-distgit']
            distgit_str = 'master-distgit'
        except KeyError:
            raise exception.InvalidUsage(
                msg="-m/--use-master-distgit used but 'master-distgit' "
                    "missing in rdoinfo for package: %s" % package)
    else:
        distgit = pkg['distgit']
        distgit_str = 'distgit'
    log.info("Cloning {dg} into ./{t.bold}{pkg}{t.normal}/".format(
        t=log.term, dg=distgit_str, pkg=package))
    patches = pkg.get('patches')
    upstream = pkg.get('upstream')
    review_patches = pkg.get('review-patches')
    review_origin = pkg.get('review-origin')

    git('clone', distgit, package)
    with helpers.cdir(package):
        if gerrit_remotes:
            log.info('Adding gerrit-origin remote...')
            git('remote', 'add', 'gerrit-origin', distgit)
        if patches:
            log.info('Adding patches remote...')
            git('remote', 'add', 'patches', patches)
            if gerrit_remotes:
                log.info('Adding gerrit-patches remote...')
                git('remote', 'add', 'gerrit-patches', patches)
        else:
            log.warn("'patches' remote information not available in rdoinfo.")
        if upstream:
            log.info('Adding upstream remote...')
            git('remote', 'add', 'upstream', upstream)
        else:
            log.warn("'upstream' remote information not available in rdoinfo.")
        if patches or upstream:
            git('fetch', '--all')

        if not review_user:
            # USERNAME is an env var used by gerrit
            review_user = os.environ.get('USERNAME') or os.environ.get('USER')
        msg_user = ('Using {t.bold}{u}{t.normal} as gerrit username, '
                    'you can change it with '
                    '{t.cmd}git remote set-url {r} ...{t.normal}')
        if review_patches:
            log.info('Adding gerrit remote for patch chains reviews...')
            r = tidy_ssh_user(review_patches, review_user)
            log.info(msg_user.format(u=review_user, r='review-patches',
                                     t=log.term))
            git('remote', 'add', 'review-patches', r)
        else:
            log.warn("'review-patches' remote information not available"
                     " in rdoinfo.")
        if review_origin:
            log.info('Adding gerrit remote for reviews...')
            r = tidy_ssh_user(review_origin, review_user)
            log.info(msg_user.format(u=review_user, r='review-origin',
                                     t=log.term))
            git('remote', 'add', 'review-origin', r)
        else:
            log.warn("'review-origin' remote information not available"
                     " in rdoinfo.")
        git('remote', '-v', direct=True)


def diff(version, new_version, bump_only=False, no_diff=False,
         version_tag_style=None):
    if bump_only or no_diff:
        return
    vtag_from = guess.version2tag(version, version_tag_style)
    vtag_to = guess.version2tag(new_version, version_tag_style)
    git('--no-pager', 'diff', '--stat', '%s..%s' % (vtag_from, vtag_to),
        direct=True)
    try:
        reqdiff(vtag_from, vtag_to)
    except Exception:
        pass
    raw_input("Press <Enter> to continue after you inspected the diff. ")


def get_diff_range(diff_range=None, patches_branch=None, branch=None):
    vtag_from, vtag_to = None, None
    if diff_range:
        n = len(diff_range)
        if n > 2:
            raise exception.InvalidUsage(why="diff only supports one or two "
                                             "positional parameters.")
        if n == 2:
            vtag_from, vtag_to = diff_range
        else:
            vtag_to = diff_range[0]
    if not vtag_from:
        if not patches_branch:
            if not branch:
                branch = guess.current_branch()
            patches_branch = guess.patches_branch(branch)
        if not git.ref_exists('refs/remotes/%s' % patches_branch):
            msg = ("Patches branch not found: %s\n"
                   "Can't guess current version.\n\n"
                   "a) provide git tags/refs yourself a la:\n"
                   "   $ rdopkg reqdiff 1.1.1 2.2.2\n\n"
                   "b) add git remote with expected patches branch"
                   % patches_branch)
            raise exception.CantGuess(msg=msg)
        vtag_from = git.get_latest_tag(branch=patches_branch)
    if not vtag_to:
        upstream_branch = guess.upstream_branch()
        vtag_to = git.get_latest_tag(branch=upstream_branch)
    return {
        'version_tag_from': vtag_from,
        'version_tag_to': vtag_to
    }


def _ensure_branch(branch):
    if not branch:
        return
    if git.current_branch() != branch:
        git.checkout(branch)


def _reset_branch(branch, remote_branch):
    if git.branch_exists(branch):
        git('update-ref', 'refs/heads/%s' % branch,
            'refs/remotes/%s' % remote_branch)
    else:
        git.create_branch(branch, remote_branch)


def _is_same_commit(ref1, ref2):
    h1 = git('rev-parse', ref1, log_cmd=False)
    h2 = git('rev-parse', ref2, log_cmd=False)
    return h1 and h1 == h2


def fetch_all():
    git('fetch', '--all', direct=True)


def prep_new_patches_branch(new_version,
                            local_patches_branch, patches_branch,
                            local_patches=False, bump_only=False,
                            patches_style=None, version_tag_style=None):
    if patches_style == 'review':
        new_version_tag = guess.version2tag(new_version, version_tag_style)
        try:
            remote, branch = git.remote_branch_split(patches_branch)
            helpers.confirm("Push %s to %s/%s (with --force)?" % (
                new_version_tag, remote, branch))
            git('branch', '--force', local_patches_branch, new_version_tag)
            git('push', '--force', remote,
                '%s:%s' % (local_patches_branch, branch))
            # push the tag
            git('push', '--force', remote, new_version_tag)
        except exception.UserAbort:
            pass
    else:
        if not (local_patches or bump_only):
            _reset_branch(local_patches_branch, remote_branch=patches_branch)


def get_patches_branch(local_patches_branch, patches_branch,
                       local_patches=False, patches_style=None,
                       gerrit_patches_chain=None,
                       bump_only=False, force=False):
    if local_patches or bump_only:
        return
    if patches_style == 'review':
        if not gerrit_patches_chain:
            gerrit_patches_chain = guess.gerrit_patches_chain()
        if gerrit_patches_chain:
            rpmfactory.fetch_patches_branch(local_patches_branch,
                                            gerrit_patches_chain,
                                            force)
        else:
            log.warn("Review patches chain not found. No patches yet?")
    else:
        _reset_branch(local_patches_branch, remote_branch=patches_branch)


def checkout_patches_branch(local_patches_branch):
    git.checkout(local_patches_branch)


def review_patches_branch(local_patches_branch, patches_style=None,
                          bump_only=False):
    if patches_style != 'review' or bump_only:
        return
    try:
        helpers.confirm("Send %s branch for review?" % local_patches_branch)
        rpmfactory.review_patch(local_patches_branch)
    except exception.UserAbort:
        pass


def rebase_patches_branch(new_version, local_patches_branch,
                          patches_branch=None, local_patches=False,
                          patches_style=None, version_tag_style=None,
                          bump_only=False):
    if bump_only:
        return
    git.checkout(local_patches_branch)
    new_version_tag = guess.version2tag(new_version, version_tag_style)
    git('rebase', new_version_tag, direct=True)

    if patches_style != 'review':
        if local_patches or not patches_branch:
            return
        if _is_same_commit(local_patches_branch, patches_branch):
            log.info("%s is up to date, no need for push." % patches_branch)
            return
        try:
            remote, branch = git.remote_branch_split(patches_branch)
            helpers.confirm("Push %s to %s / %s (with --force)?" % (
                local_patches_branch, remote, branch))
            git('push', '--force', remote,
                '%s:%s' % (local_patches_branch, branch))
            # push the tag
            git('push', '--force', remote, new_version_tag)
        except exception.UserAbort:
            pass


def check_new_patches(version, local_patches_branch,
                      patches_style=None, local_patches=False,
                      patches_branch=None, changes=None,
                      version_tag_style=None):
    if not changes:
        changes = []
    if local_patches or patches_style == 'review':
        head = local_patches_branch
    else:
        if not patches_branch:
            raise exception.RequiredActionArgumentNotAvailable(
                action='check_new_patches', arg='patches_branch')
        head = patches_branch

    version_tag = guess.version2tag(version, version_tag_style)
    patches = git.get_commit_bzs(version_tag, head)
    spec = specfile.Spec()

    n_git_patches = len(patches)
    n_spec_patches = spec.get_n_patches()
    n_skip_patches = spec.get_n_excluded_patches()
    n_ignore_patches = 0

    ignore_regex = spec.get_patches_ignore_regex()
    if ignore_regex:
        patches = (flatten(_partition_patches(patches, ignore_regex)))
        n_ignore_patches = n_git_patches - len(patches)

    patch_subjects = []
    for hash, subject, bzs in patches:
        subj = subject
        bzstr = ' '.join(map(lambda x: 'rhbz#%s' % x, bzs))
        if bzstr != '':
            subj += ' (%s)' % bzstr
        patch_subjects.append(subj)
    n_base_patches = n_skip_patches + n_spec_patches
    log.debug("Total patches in git:%d spec:%d skip:%d ignore:%d" % (
              n_git_patches, n_spec_patches, n_skip_patches, n_ignore_patches))

    if n_base_patches > 0:
        patch_subjects = patch_subjects[0:-n_base_patches]

    if not patch_subjects:
        log.warn("No new patches detected in %s." % head)
        helpers.confirm("Do you want to continue anyway?", default_yes=False)
    changes.extend(patch_subjects)
    return {'changes': changes}


def get_upstream_patches(version, local_patches_branch,
                         patches_branch=None, upstream_branch=None,
                         new_milestone=None):
    # TODO: nuke this, looks unused
    patches = git("log", "--cherry-pick", "--pretty=format:\%s",
                  "%(remote)s...%(local)s" % {'remote': patches_branch,
                                              'local': local_patches_branch})
    changes = [p.strip().replace('\\', '')
               for p in patches.split('\n') if p != '']

    if not changes:
        log.warn("No new patches detected in %s." % local_patches_branch)
        helpers.confirm("Do you want to continue anyway?", default_yes=False)

    n_patches = len(changes)
    changes.insert(0, ("Rebase %s changes from %s" %
                       (n_patches, upstream_branch)))
    args = {'changes': changes}
    if n_patches > 0:
        if new_milestone:
            new_milestone += '.p%d' % n_patches
        else:
            new_milestone = 'p%d' % n_patches
        args['new_milestone'] = new_milestone
    return args


def update_spec(branch=None, changes=None,
                new_rpm_version=None, new_release=None,
                new_milestone=None, new_patches_base=None):
    if not changes:
        changes = []
    _ensure_branch(branch)
    spec = specfile.Spec()
    if new_rpm_version:
        old_version = spec.get_tag('Version')
        if specfile.has_macros(old_version):
            log.info('Version contains macro - not touching that.')
        else:
            spec.set_tag('Version', new_rpm_version)
    if new_release is not None:
        if spec.recognized_release():
            spec.set_release(new_release, milestone=new_milestone)
        else:
            log.info('Custom Release format detected '
                     '- assuming custom milestone management.')
            spec.set_release(new_release)
    else:
        spec.bump_release(milestone=new_milestone)
    if new_patches_base:
        if new_patches_base == new_rpm_version:
            new_patches_base = None
        changed = spec.set_patches_base_version(new_patches_base)
        if not changed:
            log.info("Macro detected in patches_base - not touching that.")
    spec.new_changelog_entry(user=guess.user(), email=guess.email(),
                             changes=changes)
    spec.save()


def get_source(new_sources=False):
    if not new_sources:
        return
    source_urls = specfile.Spec().get_source_urls()
    # So far, only Source/Source0 is a tarball to download
    source_url = source_urls[0]
    source_fn = os.path.basename(source_url)
    if os.path.isfile(source_fn):
        log.info("%s already present" % source_fn)
        return
    try:
        helpers.download_file(source_url)
    except exception.CommandFailed:
        raise exception.ActionRequired(
            msg="Failed to download source tarball. Please update Source0 in "
                ".spec file.", rerun=True)


def new_sources(branch=None, fedpkg=FEDPKG, new_sources=False):
    _ensure_branch(branch)
    if not new_sources:
        return
    sources = specfile.Spec().get_source_fns()
    cmd = fedpkg + ['new-sources'] + sources
    run(*cmd, direct=True)


def _commit_message(changes=None):
    if not changes:
        _, changes = specfile.Spec().get_last_changelog_entry(strip=True)
        if not changes:
            raise exception.IncompleteChangelog()
    msg = re.sub(r'\s+\(.*\)\s*$', '', changes[0])
    fixed_rhbzs = set()
    for change in changes:
        for m in re.finditer(r'rhbz#(\d+)', change):
            fixed_rhbzs.add(m.group(1))
    if fixed_rhbzs:
        rhbzs_str = "\n".join(map(lambda x: "Resolves: rhbz#%s" % x,
                                  fixed_rhbzs))
        msg += "\n\n%s" % rhbzs_str
    if len(changes) > 1:
        changes_str = "\n".join(map(lambda x: "- %s" % x, changes))
        msg += "\n\nChangelog:\n%s" % changes_str
    return msg


def commit_distgit_update(branch=None):
    _ensure_branch(branch)
    msg = _commit_message()
    git('commit', '-a', '-F', '-', input=msg, print_output=True)


def amend():
    msg = _commit_message()
    git('commit', '-a', '--amend', '-F', '-', input=msg, print_output=True)
    print("")
    git('--no-pager', 'log', '--name-status', 'HEAD~..HEAD', direct=True)


def _partition_patches(patches, regex):
    if regex is None:
        return [patches]

    def take(_patch):
        return not bool(regex.search(_patch[1]))

    def _stacker(buckets):
        while True:
            item, new_bucket = yield
            if new_bucket:
                buckets.append([item])
            else:
                buckets[-1].append(item)

    def _filter(check, stacker):
        start_bucket = True
        while True:
            item = yield
            if check(item):
                stacker.send((item, start_bucket))
                start_bucket = False
            else:
                start_bucket = True

    buckets = []
    stacker = _stacker(buckets)
    stacker.next()
    filter = _filter(take, stacker)
    filter.next()

    for patch in patches:
        filter.send(patch)
    return buckets


def flatten(list_of_lists):
    return list(itertools.chain(*list_of_lists))


def update_patches(branch, local_patches_branch,
                   version=None, new_version=None, version_tag_style=None,
                   amend=False, bump_only=False):
    if bump_only:
        return
    target_version = new_version or version
    if not target_version:
        raise exception.RequiredActionArgumentNotAvailable(
            action='update_patches',
            arg='version or new_version')
    tag = guess.version2tag(target_version, version_tag_style)
    _ensure_branch(local_patches_branch)
    patches = git.get_commits(tag, local_patches_branch)
    n_patches = len(patches)
    _ensure_branch(branch)
    spec = specfile.Spec()
    spec.sanity_check()
    patches_base, n_excluded = spec.get_patches_base()
    ignore_regex = spec.get_patches_ignore_regex()
    if not ignore_regex:
        log.info('No valid patch filtering regex found in the spec file.')
    if ignore_regex and patches_base is None:
        raise exception.OnlyPatchesIgnoreUsed()

    patch_fns = spec.get_patch_fns()
    for pfn in patch_fns:
        git('rm', '--ignore-unmatch', pfn)
    patch_fns = []

    if n_excluded > 0:
        patches = patches[:-n_excluded]
    patches.reverse()

    ranges = [patches]
    filtered_patches = patches
    if ignore_regex:
        ranges = _partition_patches(patches, ignore_regex)
        filtered_patches = flatten(ranges)
    n_filtered_out = len(patches) - len(filtered_patches)

    log.info(
        "\n{t.bold}{n} patches{t.normal} on top of {t.bold}{tag}{t.normal}"
        ", {t.bold}{ne}{t.normal} excluded by base"
        ", {t.bold}{nf}{t.normal} filtered out by regex.".format(
            t=log.term,
            n=n_patches,
            tag=tag,
            ne=n_excluded,
            nf=n_filtered_out))

    if patches and filtered_patches:
        for hsh, title in reversed(filtered_patches):
            log.info("%s  %s" % (log.term.green(hsh), title))

        patch_fns = []
        for patch_range in ranges:
            start_commit, _title = patch_range[0]
            end_commit, _title = patch_range[-1]
            start_number = len(patch_fns) + 1

            rng = git.rev_range(start_commit + '~', end_commit)
            format_patch_cmd = ['format-patch', '--no-renames',
                                '--no-signature', '-N', '--ignore-submodules',
                                '--start-number', str(start_number), rng]

            o = git(*format_patch_cmd)
            range_files = git._parse_output(o)
            patch_fns.extend(range_files)

        for pfn in patch_fns:
            git('add', pfn)

    spec.set_new_patches(patch_fns)
    patches_branch_ref = git('rev-parse', local_patches_branch)
    spec.set_commit_ref_macro(patches_branch_ref)
    spec.save()
    if git.is_clean():
        log.info('No new patches.')
        return
    msg = 'Updated patches from ' + local_patches_branch
    git('commit', '-a', '-m', msg)
    if amend:
        git.squash_last()


def squash():
    git.squash_last()


def final_spec_diff(branch=None):
    _ensure_branch(branch)
    print("Important distgit changes:")
    spec = specfile.Spec()
    git('--no-pager', 'diff', 'HEAD~..HEAD', '--', spec.fn, direct=True)
    print("")
    git('--no-pager', 'log', '--name-status', 'HEAD~..HEAD', direct=True)
    print("\nRequested distgit update finished, see last commit.")


def edit_spec():
    raise exception.ActionRequired(
        msg="Edit .spec file as needed and describe changes in changelog.")


def make_srpm(package, dist=None, fedpkg=FEDPKG):
    cmd = list(fedpkg)
    if dist:
        dname, _, drls = dist.partition('-')
        if dname == 'epel' and drls:
            cmd += ['--dist', 'el' + drls]
    cmd.append('srpm')
    out = run(*cmd)
    m = re.search(r'/([^/\\]+\.src.rpm)\b', out)
    if not m:
        raise exception.CommandOutputParseError(tool=cmd[0], output=out)
    srpm = m.group(1)
    if not os.path.isfile(srpm):
        raise exception.FileNotFound(path=srpm)
    return {'srpm': srpm}


def tag_patches_branch(package, local_patches_branch, patches_branch,
                       force=False, push=False):
    """ Tag the local_patches_branch with this package's NVR. """
    nvr = specfile.Spec().get_nvr()
    nvr_tag = package + '-' + nvr
    tag_cmd = ['tag', nvr_tag, local_patches_branch]
    if force:
        tag_cmd.append('-f')
    git(*tag_cmd)
    patches_remote = patches_branch.partition('/')[0]
    if push:
        git('push', patches_remote, nvr_tag)
    else:
        print('Not pushing tag. Run "git push %s patches" by hand.' % nvr_tag)
