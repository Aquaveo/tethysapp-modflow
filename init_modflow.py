"""
********************************************************************************
* Name: init_modflow.py
* Author: nswain & ckrewson & thoang
* Created On: August 04, 2016
* Copyright: (c) Aquaveo 2016
* License:
********************************************************************************
"""
import os
import time
import django


def init(count=0):

    from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager
    from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection
    from tethysapp.modflow.app import Modflow

    session = None
    gs_engine = Modflow.get_spatial_dataset_service(Modflow.GEOSERVER_NAME, as_engine=True)
    model_db_con = ModelFileDatabaseConnection(db_dir='/tmp')
    gs_manager = ModflowSpatialManager(gs_engine, model_db_con, 'filler')

    try:
        print("Creating global layer styles in the GeoServer")
        gs_manager.create_workspace()
        gs_manager.create_all_styles()

        print("Successfully initialized the Modflow Geoserver.")
    except Exception as e:
        count += 1
        max_retries = 6
        print(str(e))
        if count <= max_retries:
            print('Retry ({}/{}) to initialize the MODFLOW Geoserver.'.format(count, max_retries))
            time.sleep(30)
            init(count=count)
        else:
            print('Failed to initialize the Modflow Geoserver due to above error after {} tries.'.format(max_retries))
            return False
    finally:
        session and session.close()

    return True


if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tethys_portal.settings'
    django.setup()
    success = init()

    if not success:
        exit(1)

    exit(0)
