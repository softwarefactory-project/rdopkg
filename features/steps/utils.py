from behave import *
import os
import re
import tempfile

from rdopkg.utils.distgitmagic import run
from rdopkg.const import STATE_FILE_FN


@when('I run rdopkg {args}')
def step_impl(context, args):
    # proper argument parsing might be needed
    cmd = ['rdopkg'] + args.split(' ')
    context.command_output = run(*cmd, fatal=False, log_fail=False)


@given('a temporary directory')
def step_impl(context):
    context.tempdir = tempfile.mkdtemp(prefix='rdopkg-test-')
    context.old_cwd = os.getcwd()
    os.chdir(context.tempdir)


@then("command output contains '{rex}'")
def step_impl(context, rex):
    assert re.search(rex, context.command_output), \
        "Did not find [{0}] in command output [{1}]".format(
            rex, context.command_output.encode('ascii', 'replace'))


@then("command return code is {n:n}")
def step_impl(context, n):
    rc = context.command_output.return_code
    assert n == rc, \
        "Command return code is %s but should be %s" % (rc, n)


@then(u'rdopkg state file is present')
def step_check_for_rdopkg_state_file_not_present(context):
    assert os.path.exists(os.path.join(context.distgitdir, STATE_FILE_FN))


@then(u'rdopkg state file is not present')
def step_check_for_rdopkg_state_file_not_present(context):
    assert not os.path.exists(os.path.join(context.distgitdir, STATE_FILE_FN))
