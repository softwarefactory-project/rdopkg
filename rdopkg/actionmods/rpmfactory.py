"""RPMFactory-related actions."""


from rdopkg.utils import log
from rdopkg.utils.cmd import git
from rdopkg import guess


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
    git("review", "-r", "review-patches", "-d", _patchset)
