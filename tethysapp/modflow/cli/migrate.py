"""
********************************************************************************
* Name: migrate
* Author: nswain
* Created On: May 11, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import alembic.config as ac
from tethysapp.modflow.cli.cli_helpers import print_success, print_header
APP_NAME = 'modflow'


def migrate(arguments):
    """
    Handle migration command.
    """
    if arguments.downgrade:
        header_message = 'Applying downgrade migration '
    else:
        header_message = 'Applying upgrade migration '

    if arguments.revision:
        header_message += 'with revision "{}" '.format(arguments.revision)

    header_message += 'for app "{}"...'.format(APP_NAME)
    print_header(header_message)

    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(root_dir, 'models', 'migration', 'alembic.ini')

    if arguments.downgrade:
        migration_operation = 'downgrade'
    else:
        migration_operation = 'upgrade'

    # Prepare alembic arguments
    alembic_args = [
        '-c', config_path,
        '-x', 'dburl={}'.format(arguments.dburl),
        migration_operation,
        arguments.revision
    ]

    ac.main(alembic_args)

    print_success('Successfully applied migrations for "{}".'.format(APP_NAME))
