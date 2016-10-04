"""
review workflow actions (rpmfactory, review.rdoproject.org)
"""

from rdopkg import guess
from rdopkg.actionmods import rpmfactory
from rdopkg.utils.cmd import git


def review_patch(local_patches_branch=None):
    if not local_patches_branch:
        local_patches_branch = git.current_branch()
        if not local_patches_branch.endswith('-patches'):
            br = guess.patches_branch(local_patches_branch)
            if br:
                local_patches_branch = br.partition('/')[2]
    rpmfactory.review_patch(local_patches_branch)


def review_spec(branch):
    rpmfactory.review_spec(branch)
