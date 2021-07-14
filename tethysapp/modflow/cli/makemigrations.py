"""
********************************************************************************
* Name: makemigrations
* Author: nswain
* Created On: May 11, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import alembic.config as ac
from tethysapp.modflow.cli.cli_helpers import print_header, print_success, print_warning
APP_NAME = 'modflow'


def makemigrations(arguments):
    """
    Handle makemigrations command.
    """
    if arguments.message:
        print_header('Generating migration for "{}" with message "{}"...'.format(APP_NAME, arguments.message))
    else:
        print_header('Generating migration for "{}"...'.format(APP_NAME))
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(root_dir, 'models', 'migration', 'alembic.ini')

    # Prepare alembic arguments
    alembic_args = [
        '-c', config_path,
        '-x', 'dburl={}'.format(arguments.dburl),
        'revision',
        '--autogenerate',
    ]

    if arguments.message:
        alembic_args.extend(['-m', arguments.message])

    ac.main(alembic_args)

    print_success('Successfully generated migrations for "{}".'.format(APP_NAME))
    print_warning(
        "IMPORTANT: Edit the generated migration! Autogenteration has major limitations and is often wrong. see: "
        "http://alembic.zzzcomputing.com/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-"
        "not-detect"
    )
