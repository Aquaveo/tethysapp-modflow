"""
********************************************************************************
* Name: __init__.py
* Author: nswain
* Created On: May 11, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import argparse
from tethysapp.modflow.cli.makemigrations import makemigrations as mm
from tethysapp.modflow.cli.migrate import migrate as mg
from tethysapp.modflow.cli.init_command import init_modflow
from tethysapp.modflow.cli.link_databases import link_databases as ld


def modflow_command():
    """
    modflow commandline interface function.
    """
    # Create parsers
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Commands')

    # makemigrations command
    makemigrations_parser = subparsers.add_parser(
        'makemigrations',
        help="Create new database migrations for modflow models."
    )
    makemigrations_parser.add_argument(
        'dburl',
        help='SQLAlchemy url to database used to compare for autogeneration of migration operations.'
    )
    makemigrations_parser.add_argument('-m', dest='message', help="Brief description of revisions.")
    makemigrations_parser.set_defaults(func=mm, message=None)

    # migrate command
    migrate_parser = subparsers.add_parser('migrate', help="Apply database migrations for modflow models.")
    migrate_parser.add_argument('dburl', help='SQLAlchemy url to database to be migrated.')
    migrate_parser.add_argument('-r', '--revision', help='Revision identifier to migrate to. Defaults to "head".')
    migrate_parser.add_argument(
        '-d', '--downgrade',
        action='store_true',
        help='Perform downgrade migration instead of upgrade migration. Specify revision when using this option.'
    )
    migrate_parser.set_defaults(func=mg, revision='head')

    # Link database command

    linkdb_parser = subparsers.add_parser('linkdb', help="Links the Modflow database to the App.")
    linkdb_parser.add_argument('service_name', help='ps_database_service_name')
    linkdb_parser.set_defaults(func=ld)

    # init command
    init_parser = subparsers.add_parser('init', help="Initialize the modflow app.")
    init_parser.add_argument('gsurl', help='GeoServer url to geoserver rest endpoint '
                                           '(e.g.: "geoserver://admin:geoserver@localhost:8181/geoserver/rest").')
    init_parser.set_defaults(func=init_modflow)

    args = parser.parse_args()
    args.func(args)
