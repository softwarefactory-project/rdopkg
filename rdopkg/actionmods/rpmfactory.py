"""RPMFactory-related actions."""


from rdopkg.utils import log
from rdopkg.utils.cmd import git, GerritQuery
from rdopkg import guess, helpers, exception


def prepare_patch_chain(spec):
    patch_files = spec.get_patch_fns()
    if not patch_files:
        log.info("There are no patches for this project yet")
        spec_branch = guess.current_branch()
        if spec_branch:
            try:
                b = 'remotes/review-patches/%s-patches' % spec_branch[4:]
                git.checkout(b)
                return
            except:
                log.error('%s does not seem to be associated '
                          'to a valid release' % spec_branch)
            return
    gerrit_host, gerrit_port = guess.gerrit_from_repo()
    project = guess.project_from_repo()
    assumed_last_patch = guess.last_patch(patch_files)
    log.info('Assumed last patch is %s' % assumed_last_patch)
    with open(assumed_last_patch, 'r') as f:
        contents = f.read()
    candidate, number = guess.patch_on_gerrit(contents,
                                              project,
                                              gerrit_host,
                                              gerrit_port)
    if not candidate:
        log.warn("Patch chain not found :(")
        return
    _patchset = candidate['number']
    if number:
        _patchset = _patchset + ',' + number
    log.info("found patch %s (%s)" % (_patchset, candidate['url']))
    git("review", "-r", "review-patches", "-d", _patchset, direct=True)


def review_patch(branch):
    # this is just an alias easier to remember for the git review command
    # it assumes a commit was done and ready to be committed
    if not branch:
        branch = guess.current_branch()
    if not branch.endswith('patches'):
        branch = '%s-patches' % branch
    git("review", "-y", "-r", "review-patches", branch, direct=True)


def fetch_patches_branch(local_patches_branch, gerrit_patches_chain=None,
                         force=False):
    git('fetch', 'patches', 'refs/changes/' + gerrit_patches_chain)
    patch_commit = git('rev-parse', 'FETCH_HEAD')
    gerrit_host, gerrit_port = guess.gerrit_from_repo()
    q = GerritQuery(gerrit_host, gerrit_port)
    review = q('--current-patch-set', 'commit:%s' % patch_commit)
    approvals = review.get('currentPatchSet', {}).get('approvals', [])
    jenkins = [a for a in approvals
               if a.get('type') == 'Verified' and
               a.get('by', {}).get('username') == 'jenkins']
    if not jenkins:
        verified = 0
    else:
        verified = int(jenkins[0]['value'])
    if verified != 1:
        if force:
            log.warn(
                "Ref %s has not been validated by CI" % gerrit_patches_chain)
            helpers.confirm("Do you want to continue anyway?",
                            default_yes=False)
        else:
            raise exception.UnverifiedPatch()
    git.checkout(local_patches_branch)
    git('reset', '--hard', 'FETCH_HEAD')


def review_spec(branch):
    # this is just an alias easier to remember for the git review command
    # it assumes a commit was done and ready to be committed
    if not branch:
        branch = guess.current_branch()
    git("review", "-r", "review-origin", branch, direct=True)
