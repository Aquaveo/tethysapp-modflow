import os
import django
from sqlalchemy import create_engine
from tethysapp.modflow.cli.cli_helpers import print_header, print_success, print_info, print_error


def link_databases(arguments):

    print_header('Linking DB for Modflow...')

    os.environ['DJANGO_SETTINGS_MODULE'] = 'tethys_portal.settings'
    django.setup()

    from tethys_apps.utilities import create_ps_database_setting, link_service_to_app_setting
    from tethysapp.modflow.app import Modflow

    print_info('Connecting to database server')

    db_server_url = str(Modflow.get_persistent_store_connection(Modflow.MODEL_DB_CON_01, as_url=True))
    engine = create_engine(db_server_url)  # This connects you to the server

    print_info('Querying database')

    result = engine.execute(
        "SELECT datname "  # noqa
        "FROM pg_database "  # noqa
        "WHERE datistemplate = false "  # noqa
        "AND datname SIMILAR TO 'modflow_\w{8}_\w{4}_\w{4}_\w{4}_\w{12}' "  # noqa
        "AND datname != 'modflow_primary';"  # noqa
    )
    model_dbs = [r[0].replace('modflow_', '') for r in result]
    result.close()

    if len(model_dbs) == 0:
        print_error('No results found')

    for db in model_dbs:
        print_info('Linking databases')
        create_success = create_ps_database_setting(Modflow.package,
                                                    db,
                                                    initialized=True,
                                                    spatial=True,
                                                    dynamic=True)
        if create_success:
            link_service_to_app_setting('persistent', arguments.service_name, Modflow.package, 'ps_database', db)
            print_success('Successfully linked Modflow DB')
        else:
            print_error('Could not link the database')
