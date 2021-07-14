"""
********************************************************************************
* Name: project_upload
* Author: ckrewson
* Created On: February 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from tethys_sdk.jobs import CondorWorkflowJobNode
from tethysapp.modflow.app import Modflow as app
from tethys_sdk.compute import get_scheduler


class ProjectUploadWorkflow(object):
    """
    Helper class that prepares and submits the new project upload jobs and workflow.
    """
    WORKFLOW_ID = 'upload'

    def __init__(self, user, workspace, workflow_name, input_archive_path, xll, yll, rotation, model_units,
                 model_version, srid, resource_db_url, resource_id, scenario_id, model_db, gs_engine, app_package):
        """
        Constructor.

        Args:
            user(auth.User): Django user.
            workflow_name(str): Name of the job.
            input_archive_path(str): Path to input zip archive.
            xll(float): lower left x coordinate for model
            yll(float): lower left y coordinate for model
            rotation: model rotation (counter clockwise)
            model_units(str): model units (feet or meters)
            model_version(str): modflow version for this model (i.e mfnwt, mf2000, mf2005, ect)
            srid(str): srid
            resource_db_url(str): SQLAlchemy url to Resource database.
            resource_id(str): ID of associated resource.
            scenario_id(int): ID of the scenario.
            model_db(ModelDatabase): ModelDatabase instance bound to model database.
            gs_engine(GeoServerSpatialDatasetSerivcesEngine): GeoServer connection object.
            app_package(str): app package for the App (i.e modflow).
        """  # noqa: E501

        self.user = user
        self.workspace = workspace
        self.job_name = workflow_name
        self.safe_job_name = ''.join(s for s in self.job_name if s.isalnum())  #: Safe name with only A-Z 0-9
        self.input_archive_path = input_archive_path
        self.xll = xll
        self.yll = yll
        self.rotation = rotation
        self.model_units = model_units
        self.model_version = model_version
        self.srid = srid
        self.resource_db_url = resource_db_url
        self.resource_id = resource_id
        self.scenario_id = scenario_id
        self.model_db = model_db
        self.gs_engine = gs_engine
        self.app_package = app_package
        self.workflow = None

    def prepare(self):
        """
        Prepares condor job for execution.
        """
        job_manager = app.get_job_manager()
        scheduler = get_scheduler(app.SCHEDULER_NAME)
        minx = app.get_custom_setting('minx_extent')
        miny = app.get_custom_setting('miny_extent')
        maxx = app.get_custom_setting('maxx_extent')
        maxy = app.get_custom_setting('maxy_extent')

        # Creating Condo Workflow
        self.workflow = job_manager.create_job(
            name=self.safe_job_name,
            user=self.user,
            job_type='CONDORWORKFLOW',
            scheduler=scheduler,
            workspace=self.workspace
        )
        self.workflow.save()

        app_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        job_executables_dir = os.path.join(app_root_dir, 'job_executables')

        # Creating Condo Workflow Job Node
        prepare_geoserver_layer_job = CondorWorkflowJobNode(
            name='prepare_geoserver_layer_job',
            workflow=self.workflow,
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=[
                os.path.join(job_executables_dir, 'geoserver_layers_executable.py'),
                os.path.join(job_executables_dir, 'update_resource_status.py'),
                self.input_archive_path
            ],
            post_script='update_resource_status.py',
            attributes=dict(
                executable='geoserver_layers_executable.py',
            )
        )

        # Setting appropriate arguments for the prepare_geoserver_layer executable
        prepare_geoserver_layer_job.set_attribute('arguments', (
            self.resource_db_url,
            self.resource_id,
            '{}_{}'.format(self.app_package, self.model_db.get_id()),
            self.xll,
            self.yll,
            self.rotation,
            self.model_units,
            self.model_version,
            self.srid,
            minx,
            maxx,
            miny,
            maxy,
            self.gs_engine.endpoint,
            self.gs_engine.public_endpoint,
            self.gs_engine.username,
            self.gs_engine.password,
            'ALL',
            ModflowModelResource.UPLOAD_GS_STATUS_KEY
        ))

        # Files to be transferred to condor machine
        input_archive_filename = os.path.basename(self.input_archive_path)
        prepare_geoserver_layer_job.set_attribute('transfer_input_files', ('../{0}'.format(input_archive_filename),))
        prepare_geoserver_layer_job.save()

        self.workflow.extended_properties['resource_id'] = str(self.resource_id)
        self.workflow.save()

    def run_job(self):
        """
        Executes the prepared job.
        """
        resource_db_session = None

        try:
            resource_db_engine = create_engine(self.resource_db_url)
            make_resource_db_session = sessionmaker(bind=resource_db_engine)
            resource_db_session = make_resource_db_session()
            resource = resource_db_session.query(ModflowModelResource).get(self.resource_id)

            resource.set_status(ModflowModelResource.ROOT_STATUS_KEY, ModflowModelResource.STATUS_PENDING)
            resource_db_session.commit()

            self.prepare()
            self.workflow.execute()
        finally:
            resource_db_session and resource_db_session.close()
