# -*- coding: UTF-8 -*-
import os
import shutil


def clean_tempdir(context, scenario):
    """
    Clean up temporary test dirs for passed tests.

    Leave failed test dirs for manual inspection.

    """
    tempdir = getattr(context, 'tempdir', None)
    if tempdir and scenario.status == 'passed':
        shutil.rmtree(tempdir)
        del(context.tempdir)


def restore_cwd(context):
    """
    Return to original working dir or behave gets confused :-/
    """
    old_cwd = getattr(context, 'old_cwd', None)
    if old_cwd:
        os.chdir(old_cwd)


def after_scenario(context, scenario):
    clean_tempdir(context, scenario)
    restore_cwd(context)
