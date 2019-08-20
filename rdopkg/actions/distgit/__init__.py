from rdopkg.action import Action, Arg


_SHARED_HELP = {
    'release_bump_index':
        ("specify which Release part to bump:\n"
         "-R MAJOR/-R MINOR/-R PATCH\n"
         "   to bump selected in MAJOR.MINOR.PATCH\n"
         "-R 1/-R 2/-R 3/-R 4/-R N\n"
         "   to bump 1./2./3./4./N. part (numeric index)\n"
         "-R 0\n"
         "   to disable bumping (no release bump)"
         "-R last-numeric\n"
         "   to bump last numeric only Release part (default)"),
}


ACTIONS = [
    Action('clone',
           help="clone an RDO package distgit and setup remotes",
           required_args=[
               Arg('package', positional=True, metavar='PACKAGE',
                   help="RDO package to clone (see `rdopkg info`)"),
           ],
           optional_args=[
               Arg('use_master_distgit', shortcut='-m', action='store_true',
                   help="clone 'master-distgit'"),
               Arg('gerrit_remotes', shortcut='-g', action='store_true',
                   help="create branches "
                        "'gerrit-origin' and 'gerrit-patches'"),
               Arg('review_user', shortcut='-u', metavar='USER',
                   help="gerrit username for reviews"),
               Arg('distro', shortcut='-d', metavar='DISTRO',
                   help="distroinfo configuration"),
           ]),
    Action('pkgenv', help="show detected package environment",
           steps=[
               Action('get_package_env'),
               Action('show_package_env'),
           ]),
    Action('patchlog', help="show patches branch log",
           steps=[
               Action('get_package_env'),
               Action('show_patch_log'),
           ]),
    Action('get-patches',
           help="setup local patches branch and switch to it",
           optional_args=[
               Arg('patches_branch', shortcut='-p', metavar='REMOTE/BRANCH',
                   help="remote git branch containing patches"),
               Arg('local_patches_branch', shortcut='-P',
                   metavar='LOCAL_BRANCH',
                   help="local git branch containing patches"),
               Arg('gerrit_patches_chain', shortcut='-g',
                   metavar='REVIEW_NUMBER',
                   help="top gerrit review id of the patch chain"),
               Arg('force', shortcut='-f', action='store_true',
                   help="use patch even if it was not validated in CI"),
           ],
           steps=[
               Action('get_package_env'),
               Action('ensure_patches_branch'),
               Action('get_patches_branch'),
               Action('checkout_patches_branch'),
           ]),
    Action('fix', continuable=True,
           help="change .spec file without introducing new patches",
           optional_args=[
               Arg('release_bump_index', shortcut='-R', metavar='INDEX',
                   help=_SHARED_HELP['release_bump_index']),
           ],
           steps=[
               Action('get_package_env'),
               Action('update_spec'),
               Action('edit_spec'),
               Action('commit_distgit_update'),
               Action('final_spec_diff'),
           ]),
    Action('patch',
           help="introduce new patches to the package",
           optional_args=[
               Arg('amend', shortcut='-a', action='store_true',
                   help="amend previous commit"),
               Arg('patches_branch', shortcut='-p', metavar='REMOTE/BRANCH',
                   help="remote git branch containing patches"),
               Arg('local_patches_branch', shortcut='-P',
                   metavar='LOCAL_BRANCH',
                   help="local git branch containing patches"),
               Arg('local_patches', shortcut='-l', action='store_true',
                   help="don't reset local patches branch, use it as is"),
               Arg('gerrit_patches_chain', shortcut='-g',
                   metavar='REVIEW_NUMBER',
                   help="top gerrit review id of the patch chain"),
               Arg('force', shortcut='-f', action='store_true',
                   help="use patch even if it was not validated in CI"),
               Arg('release_bump_index', shortcut='-R', metavar='INDEX',
                   help=_SHARED_HELP['release_bump_index']),
               Arg('no_bump', shortcut='-B', action='store_true',
                   help="don't bump release and generate changelog "
                        "(update patches only)"),
               Arg('changelog', shortcut='-C',
                   choices=['detect', 'count', 'plain'],
                   help="how to generate changelog from patches"),
               Arg('commit_header_file', shortcut='-H', metavar='FILE',
                   help="start commit message with FILE contents, "
                        "- for stdin"),
               Arg('changelog_user', shortcut='-u', default=None,
                   help="User to be used in new changelog entry"),
               Arg('changelog_email', shortcut='-e', default=None,
                   help="email address to be used in new changelog entry"),
           ],
           steps=[
               Action('get_package_env'),
               Action('ensure_patches_base_ref'),
               Action('ensure_patches_branch'),
               Action('get_patches_branch'),
               Action('check_new_patches'),
               Action('update_patches'),
               Action('ensure_patches_changed'),
               Action('update_spec'),
               Action('commit_distgit_update'),
               Action('final_spec_diff'),
           ]),
    Action('update_patches',
           alias='patch',
           help='Alias for `rdopkg patch --local-patches --no-bump`',
           description=(
               "A legacy backward compatibility"
               "with ancient update-patches.sh script."
           ),
           const_args={
               'local_patches': True,
               'no_bump': True,
           }),
    Action('new_version', continuable=True,
           help="update package to new upstream version",
           optional_args=[
               Arg('new_version', positional=True, nargs='?',
                   help="version to update to"),
               Arg('patches_branch', shortcut='-p', metavar='REMOTE/BRANCH',
                   help="remote git branch containing patches"),
               Arg('local_patches_branch', shortcut='-P',
                   metavar='LOCAL_BRANCH',
                   help="local git branch containing patches"),
               Arg('local_patches', shortcut='-l', action='store_true',
                   help="don't reset local patches branch, use it as is"),
               Arg('bump_only', shortcut='-b', action='store_true',
                   help="only bump .spec to new version a la rpmdev-bumpspec"),
               Arg('no_diff', shortcut='-d', action='store_true',
                   help="don't show git/requirements diff"),
               Arg('new_sources', shortcut='-N', action='store_true',
                   help=("run `fedpkg new-sources`"
                         " (default: depends on branch name)")),
               Arg('no_new_sources', shortcut='-n', action='store_true',
                   help=("don't run `fedpkg new-sources`"
                         " (default: depends on branch name)")),
               Arg('unattended', shortcut='-U', action='store_true',
                   help="don't ask any questions (NOT RECOMMENDED)"),
               Arg('no_push_patches', shortcut='-t', action='store_true',
                   help="don't push patches branch"),
               Arg('bug', shortcut='-B', metavar='BUG(S)',
                   help="reference BUG(S) in changelog. (example:"
                        " --bug rhbz#1234,rhbz#5678)"),
               Arg('commit_header_file', shortcut='-H', metavar='FILE',
                   help="start commit message with FILE contents, "
                        "- for stdin"),
               Arg('changelog_user', shortcut='-u', default=None,
                   help="User to be used in new changelog entry"),
               Arg('changelog_email', shortcut='-e', default=None,
                   help="email address to be used in new changelog entry"),
           ],
           steps=[
               Action('get_package_env'),
               Action('ensure_patches_base_ref'),
               Action('new_version_setup'),
               Action('diff'),
               Action('prep_new_patches_branch'),
               Action('get_patches_branch'),
               Action('rebase_patches_branch'),
               Action('update_patches'),
               Action('update_spec'),
               Action('get_source'),
               Action('new_sources'),
               Action('commit_distgit_update'),
               Action('final_spec_diff'),
               Action('review_patches_branch')
           ]),
    Action('amend',
           help="amend last commit and recreate commit message",
           optional_args=[
               Arg('commit_header_file', shortcut='-H', metavar='FILE',
                   help="start commit message with FILE contents, "
                        "- for stdin"),
           ]),
    Action('squash',
           help="squash HEAD into HEAD~ using HEAD~ commit message"),
    Action('get_source', help="fetch source archive",
           steps=[
               Action('get_source', const_args={'new_sources': True})
           ]),
    Action('tag_patches',
           help='tag the -patches branch in Git with the current NVR',
           optional_args=[
               Arg('force', shortcut='-f', action='store_true',
                   help='replace an existing tag with this name'),
               Arg('push', shortcut='-p', action='store_true',
                   help='push this new tag to the patches remote'),
           ],
           steps=[
               Action('get_package_env'),
               Action('ensure_patches_branch'),
               Action('tag_patches_branch'),
           ]),
    Action('set_magic_comment',
           help='set magic comment in the spec file to a value',
           required_args=[
               Arg('magic', positional=True,
                   help="Magic comment to insert"),
               Arg('value', positional=True,
                   help="Value to insert as magic comment"),
           ],
           steps=[
               Action('set_magic'),
           ]),
]
