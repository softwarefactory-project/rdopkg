from behave import *
import re
import os

from rdopkg.utils import distgitmagic
from rdopkg.utils import specfile
from rdopkg.utils.distgitmagic import git, run


@given('a distgit at Version {version} and Release {release}')
def step_impl(context, version, release):
    name = 'foo-bar'
    context.execute_steps(u'Given a temporary directory')
    context.distgitdir = distgitmagic.create_sample_distgit(
        name, version=version, release=release)
    os.chdir(context.distgitdir)
    # collect .spec state to compare against after actions
    spec = specfile.Spec()
    context.old_changelog_entry = spec.get_last_changelog_entry()
    context.old_commit = git.current_commit()


@given('a distgit at Version {version}')
def step_impl(context, version):
    step = u'Given a distgit at Version %s and Release 2' % version
    context.execute_steps(step)


@given('a distgit')
def step_impl(context):
    context.execute_steps(u'Given a distgit at Version 1.2.3 and Release 2')


@given('a patches branch with {n:n} patches')
def step_impl(context, n):
    distgitmagic.create_sample_patches_branch(n)


@given('a new version {version} with {n:n} patches from patches branch')
def step_impl(context, version, n):
    distgitmagic.create_sample_upstream_new_version(version, 9, n)


@given('a new version {version}')
def step_impl(context, version):
    context.execute_steps(
        u'Given a new version %s with 0 patches from patches branch' %
        version)


@given(u'a local file {fn} containing "{text}"')
def step_impl(context, fn, text):
    with open(os.path.join(context.distgitdir, fn), 'w') as f:
        f.write(text)


@when('I change .spec file tag {tag} to {value}')
def step_impl(context, tag, value):
    spec = specfile.Spec()
    spec.set_tag(tag, value)
    spec.save()


@when(u'I undo all changes')
def step_impl(context):
    git("stash")
    assert git.is_clean()


@when('I add description to .spec changelog')
def step_impl(context):
    spec = specfile.Spec()
    spec._txt, n = re.subn('(\n%changelog\n\*[^\n]+\n)\n',
                           '\g<1>- Description of a change\n',
                           spec.txt)
    assert n == 1
    spec.save()


@then('.spec file tag {tag} is {value}')
def step_impl(context, tag, value):
    spec = specfile.Spec()
    assert spec.get_tag(tag) == value, \
        "{0} != {1}".format(spec.get_tag(tag), value)


@then('.spec file contains new changelog entry with {n:n} lines')
def step_impl(context, n):
    spec = specfile.Spec()
    entry = spec.get_last_changelog_entry()
    assert len(entry[1]) == n
    assert entry != context.old_changelog_entry


@then('.spec file doesn\'t contain new changelog entries')
def step_impl(context):
    entry = specfile.Spec().get_last_changelog_entry()
    assert entry == context.old_changelog_entry


@then('.spec file contains new changelog entry with {text}')
def step_impl(context, text):
    spec = specfile.Spec()
    entry = spec.get_last_changelog_entry()
    changelog_block = '\n'.join(entry[1])
    assert text in changelog_block, \
        "[{0}] not found in [{1}]".format(text, changelog_block)
    assert entry != context.old_changelog_entry


@then('.spec file has {n:n} patches defined')
def step_impl(context, n):
    spec = specfile.Spec()
    assert spec.get_n_patches() == n


@then('.spec file doesn\'t contain patches_base')
def step_impl(context):
    spec = specfile.Spec()
    assert spec.get_patches_base() == (None, 0)


@then('new commit was created')
def step_impl(context):
    new_commit = git.current_commit()
    assert new_commit != context.old_commit


@then(u'no new commit was created')
def step_impl(context):
    new_commit = git.current_commit()
    assert new_commit == context.old_commit


@then(u'last commit message contains {simple_string}')
def step_impl(context, simple_string):
    msg = git.current_commit_message()
    assert simple_string in msg, \
        (u"'{0}' not found in:\n{1}".format(simple_string, msg)
         ).encode('ascii', 'replace')


@then(u'last commit message is')
def step_impl(context):
    msg = git.current_commit_message()
    assert context.text == msg, \
        (u"Commit message differs from expected format.\n"
         "\n---EXPECTED:---\n{0}\n"
         "\n---FOUND:---\n{1}".format(context.text, msg)
         ).encode('ascii', 'replace')
