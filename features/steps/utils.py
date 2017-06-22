from behave import *
import os
import tempfile

from rdopkg.utils.distgitmagic import run


@when('I run rdopkg {args}')
def step_impl(context, args):
    # proper argument parsing might be needed
    cmd = ['rdopkg'] + args.split(' ')
    run(*cmd)


@given('a temporary directory')
def step_impl(context):
    context.tempdir = tempfile.mkdtemp(prefix='rdopkg-test-')
    context.old_cwd = os.getcwd()
    os.chdir(context.tempdir)
