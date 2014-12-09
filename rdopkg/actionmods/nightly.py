from rdopkg.utils import exception
from rdopkg.utils.cmd import git
from rdopkg.utils import specfile


def get_discarded_range(stable_tag, n_commits):
    """Get the commit hashes of the first and last commit that are supposed
    to be discarded as specified in the specfile's patches_base
    """
    first_commit = None
    last_commit = None
    # assign None if there's no discarded commit in patches_base
    if n_commits:
        commits = git.get_commit_hashes(stable_tag)
        first_commit = commits[-n_commits:][-1]
        last_commit = commits[-n_commits:][0]
    return first_commit, last_commit


def rebase_nightly(upstream_branch, patches_branch, distgit_branch=None,
                   lame_patches=None):
    spec = specfile.Spec()
    stable_tag, n_commits = spec.get_patches_base()

    if not distgit_branch:
        distgit_branch = git.current_branch()

    # tmp branches
    tmp_patches_branch = "tmp-" + patches_branch
    tmp_upstream_branch = "tmp-" + upstream_branch
    # nightly_parent serves to keep the parrent commit (patches_base)
    # everything will be rebased on top of it
    nightly_parent = "nightly-parent"

    # create the temporary branches
    git.create_branch(tmp_upstream_branch, upstream_branch)
    git.create_branch(tmp_patches_branch, patches_branch)

    git.checkout(tmp_upstream_branch)

    if lame_patches is not None:
        for commit in lame_patches:
            git.remove(commit)

    git.linearize(stable_tag)

    try:
        git.checkout(tmp_patches_branch)
        first_commit, last_commit = get_discarded_range(stable_tag,
                                                        n_commits)
        # remove the discarded commits defined in the specfile from the
        # tmp patches branch
        if first_commit is not None:
            git('rebase', '--onto', first_commit + '^', last_commit,
                '--strategy', 'recursive', '-X', 'ours')
            git.create_branch(nightly_parent, last_commit)

        # add stable commits below downstream patches
        git('rebase', tmp_upstream_branch)

        if first_commit:
            # put everything on top of the commits that are discarded in
            # patches_base when running update-patches
            git('rebase', nightly_parent, '--strategy', 'recursive', '-X',
                'theirs')

        # rebase tmp patches in the patches branch
        git.checkout(patches_branch)
        git('rebase', tmp_patches_branch)
    finally:
        git.delete_branch(tmp_upstream_branch)
        git.delete_branch(tmp_patches_branch)
        git.delete_branch(nightly_parent)
    git("checkout", distgit_branch)
