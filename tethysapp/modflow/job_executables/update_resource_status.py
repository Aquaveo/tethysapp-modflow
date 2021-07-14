#!/opt/tethys-python
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource


def run(workflow, resource_db_url, resource_id):
    resource_db_session = None

    try:
        # Get resource
        resource_db_engine = create_engine(resource_db_url)
        make_resource_db_session = sessionmaker(bind=resource_db_engine)
        resource_db_session = make_resource_db_session()
        resource = resource_db_session.query(ModflowModelResource).get(resource_id)

        status_success = False

        # Get status for upload keys
        if workflow == 'upload':
            upload_status = resource.get_status(ModflowModelResource.UPLOAD_STATUS_KEY, None)
            upload_gs_status = resource.get_status(ModflowModelResource.UPLOAD_GS_STATUS_KEY, None)

            upload_status_ok = upload_status in ModflowModelResource.OK_STATUSES
            upload_gs_status_ok = upload_gs_status in ModflowModelResource.OK_STATUSES

            status_success = upload_status_ok and upload_gs_status_ok

        # Set root status accordingly
        if status_success:
            resource.set_status(ModflowModelResource.ROOT_STATUS_KEY, ModflowModelResource.STATUS_SUCCESS)
        else:
            resource.set_status(ModflowModelResource.ROOT_STATUS_KEY, ModflowModelResource.STATUS_FAILED)

        resource_db_session.commit()
    finally:
        resource_db_session and resource_db_session.close()


if __name__ == '__main__':
    args = sys.argv
    args.pop(0)
    run(*args)
