"""RPMFactory-related actions."""


from rdopkg.utils import log
from rdopkg.utils.cmd import git, GerritQuery
from rdopkg import guess, helpers, exception


def _review_number(review_ref):
    parts = review_ref.split('/')
    if len(parts) == 1:
        return review_ref
    return parts[-2]


def _review_ref(review_n, patchset_n):
    cache = review_n[-2:]
    cache = (2 - len(review_n)) * '0' + cache
    return 'refs/changes/%s/%s/%s' % (cache, review_n, patchset_n)


def review_url(review_n, gerrit_query=None, verbose=False):
    if not review_n:
        return None
    if not gerrit_query:
        gerrit_host, gerrit_port = guess.gerrit_from_repo()
        gerrit_query = GerritQuery(gerrit_host, gerrit_port, log_cmd=verbose)
    review = gerrit_query(review_n)
    return review.get('url')


def fetch_patches_branch(local_patches_branch, gerrit_patches_chain,
                         force=False):
    review_n = _review_number(gerrit_patches_chain)
    gerrit_host, gerrit_port = guess.gerrit_from_repo()
    query = GerritQuery(gerrit_host, gerrit_port)
    review = query('--current-patch-set', review_n)
    current_ps = review.get('currentPatchSet', {})
    patchset_n = current_ps.get('number')
    if not patchset_n:
        raise exception.CantGuess(
            msg='Failed to determine current patch set for review: %s'
                % gerrit_patches_chain)
    gerrit_ref = _review_ref(review_n, patchset_n)
    git('fetch', 'patches', gerrit_ref)

    approvals = current_ps.get('approvals', [])
    jenkins = [a for a in approvals
               if a.get('type') == 'Verified' and
               a.get('by', {}).get('username') == 'jenkins']
    code_reviews = [int(a.get('Value', 0)) for a in approvals
                    if a.get('type') == 'Code-Review']
    if not jenkins:
        verified = 0
    else:
        verified = int(jenkins[0]['value'])
    if verified != 1:
        if force:
            log.warn(
                "Ref %s has not been validated by CI." % gerrit_patches_chain)
            helpers.confirm("Do you want to continue anyway?",
                            default_yes=False)
        else:
            raise exception.UnverifiedPatch()
    if any(cr < 0 for cr in code_reviews):
        log.warn(
            "Ref %s has at least one negative review." % gerrit_patches_chain)
        helpers.confirm("Do you want to continue anyway?",
                        default_yes=False)

    git('update-ref', 'refs/heads/%s' % local_patches_branch,
        'FETCH_HEAD')


def review_spec(branch):
    git("review", "-r", "review-origin", branch, direct=True)


def review_patch(branch):
    git("review", "-y", "-r", "review-patches", branch, direct=True)
