from behave import *
from rdopkg.utils.cmd import run


@when(u'I run rdopkg {args}')
def step_impl(context, args):
    # NOTE(jruzicka): proper argument parsing might be needed
    cmd = ['rdopkg'] + args.split(' ')
    run(*cmd, log_cmd=False)
