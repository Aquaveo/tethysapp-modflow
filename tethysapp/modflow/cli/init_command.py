from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tethysext.atcore.utilities import parse_url
from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager
from tethysapp.modflow.cli.cli_helpers import print_header, print_success, print_info, print_error


def init_modflow(arguments):
    """
    Commandline interface for initializing the modflow app.
    """
    print_header('Initializing Modflow...')

    url = parse_url(arguments.gsurl)

    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint=url.endpoint,
        username=url.username,
        password=url.password
    )

    gsm = ModflowSpatialManager(
        geoserver_engine=geoserver_engine
    )

    # Initialize workspace
    print_info('Initializing Modflow GeoServer Workspace...')
    try:
        gsm.create_workspace()
    except Exception as e:
        print_error('An error occurred during workspace creation: {}'.format(e))
    print_success('Successfully initialized Modflow GeoServer workspace.')

    # Initialize styles
    print_info('Initializing Modflow GeoServer Styles...')
    try:
        gsm.create_all_styles(overwrite=True)
    except Exception as e:
        print_error('An error occurred during style creation: {}'.format(e))
    print_success('Successfully initialized Modflow GeoServer styles.')
    print_success('Successfully initialized Modflow.')
