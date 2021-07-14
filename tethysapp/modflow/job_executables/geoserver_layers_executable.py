#!/opt/tethys-python
import sys
import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine
from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager


def run(resource_db_url, resource_id, db_url, xll, yll, rotation, model_units, model_version, srid, minx, maxx, miny,
        maxy, geoserver_endpoint, geoserver_public_endpoint, geoserver_username, geoserver_password, geoserver_job_type,
        status_key):
    """
    Condor executable that creates the geoserver layers for GSSHA projects.

    Args:
        resource_db_url(str): SQLAlchemy url to the Resource database (e.g.: postgresql://postgres:pass@localhost:5432/db).
        resource_id(str): ID of the Resource associated with the GSSHA model.
        db_url(str): Path of the File Database.
        xll(float): lower left x coordinate for model
        yll(float): lower left y coordinate for model
        rotation(float): model rotation (counter clockwise)
        model_units(str): model units (feet or meters)
        model_version(str): modflow version for this model (i.e mfnwt, mf2000, mf2005, ect)
        srid(str): srid
        minx (str): minx for model selection map view
        maxx (str): maxx for model selection map view
        miny (str): miny, for model selection map view
        maxy (str): maxy for model selection map view
        geoserver_endpoint(str): Url to the GeoServer public endpoint (e.g.: http://localhost:8181/geoserver/rest/).
        geoserver_public_endpoint(str): Url to the GeoServer public endpoint (e.g.: https://geoserver.aquaveo.com/geoserver/rest/).
        geoserver_username(str): Administrator username for given GeoServer.
        geoserver_password(str): Administrator password for given GeoServer.
        geoserver_job_type(str): The type of GeoServer job type to run. One of 'ALL'.
        status_key(str): Name of status key to use for status updates on the Resource.
    """  # noqa: E501
    resource = None
    resource_db_session = None

    try:
        # Create ModelFileDatabaseConnection and ModflowSpatialManager
        model_db = ModelFileDatabaseConnection(db_dir=db_url)
        gs_engine = GeoServerSpatialDatasetEngine(
            endpoint=geoserver_endpoint,
            username=geoserver_username,
            password=geoserver_password
        )
        gs_engine.public_endpoint = geoserver_public_endpoint
        gs_manager = ModflowSpatialManager(gs_engine, model_db, model_version)

        # Get appropriate length units for model
        if model_units == 'feet':
            lenuni = 1
        else:
            lenuni = 2

        # Modifying Flopy model for correct spatial reference
        gs_manager.modify_spatial_reference(xll=float(xll),
                                            yll=float(yll),
                                            rotation=float(rotation),
                                            epsg=int(srid),
                                            units=model_units,
                                            lenuni=lenuni)
        gs_manager.model_selection_bounds = [minx, maxx, miny, maxy]

        # Create all geoserver layers from flopy and upload to geoserver
        _type_to_function_mapping = {
            'ALL': gs_manager.create_all,
        }

        _type_to_function_mapping[geoserver_job_type](
            reload_config=True
        )
        # get resource and update geoserver status accordingly
        resource_db_engine = create_engine(resource_db_url)
        make_session = sessionmaker()
        resource_db_session = make_session(bind=resource_db_engine)
        resource = resource_db_session.query(ModflowModelResource).get(resource_id)

        resource.set_status(status_key, ModflowModelResource.STATUS_SUCCESS)
        sys.stdout.write('\nSuccessfully processed\n')

    except Exception as e:
        # Change resource status to error
        if resource:
            resource.set_status(status_key, ModflowModelResource.STATUS_ERROR)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write(type(e).__name__)
        sys.stderr.write(repr(e))
        raise e
    finally:
        resource_db_session and resource_db_session.commit()


if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    run(*args)
