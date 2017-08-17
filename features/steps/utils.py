from behave import *
import os
import re
import tempfile

from rdopkg.utils.distgitmagic import run


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
    if not re.search(rex, context.command_output):
        print("Did not find [{0}] in command output [{1}]".format(rex, context.command_output))
    assert re.search(rex, context.command_output)
