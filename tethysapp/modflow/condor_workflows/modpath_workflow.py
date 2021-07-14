"""
********************************************************************************
* Name: modpath_workflow
* Author: ckrewson
* Created On: February 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
from tethys_sdk.jobs import CondorWorkflowJobNode
from tethysapp.modflow.app import Modflow as app
from tethys_sdk.compute import get_scheduler


class ModpathWorkflow(object):
    """
    Class Based Controller for modpath tool
    """
    WORKFLOW_ID = 'modpath'

    def __init__(self, user, workspace, session_id, lat, lon, depth, xll, yll, rotation, db_dir, model_units,
                 model_version, modflow_exe, modpath_exe, nam_file, srid, resource_id, database_id, app_package):
        """
        Constructor.

        Args:
            user(Django User): Django User
            workspace(str): 'path/to/user/workspace/session_id'
            session_id(str): Django session ID
            lat(float): flow path point latitude
            lon(float): flow path point longitude
            depth(float): flow path point depth
            xll(float): lower left x coordinate for model
            yll(float): lower left y coordinate for model
            rotation: model rotation
            db_dir(str): path to model file database directory
            model_units(str): model units (feet or meters)
            model_version(str): modflow version for this model (i.e mfnwt, mf2000, mf2005, ect)
            modflow_exe(str): path to modflow executable
            modpath_exe(str): path to modpath executable
            nam_file(str): path to "file".nam for modflow
            srid(str): srid
            resource_id (str): Resource ID
            database_id (str): Database ID for the given resource
            app_package(str): app package for the App (i.e modflow).
        """  # noqa: E501

        self.user = user
        self.workspace = workspace
        self.session_id = session_id
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.job_name = 'modpath'
        self.safe_job_name = ''.join(s for s in self.job_name if s.isalnum())  #: Safe name with only A-Z 0-9
        self.xll = xll
        self.yll = yll
        self.rotation = rotation
        self.db_dir = db_dir
        self.model_units = model_units
        self.model_version = model_version
        self.modflow_exe = modflow_exe
        self.modpath_exe = modpath_exe
        self.nam_file = nam_file
        self.srid = srid
        self.resource_id = resource_id
        self.database_id = database_id
        self.app_package = app_package
        self.workflow = None

    def prepare(self):
        """
        Prepares condor job for execution.
        """
        job_manager = app.get_job_manager()
        scheduler = get_scheduler(app.SCHEDULER_NAME)

        # Creating Condo Workflow
        self.workflow = job_manager.create_job(
            name=self.job_name,
            user=self.user,
            job_type='CONDORWORKFLOW',
            scheduler=scheduler,
            workspace=self.workspace
        )
        self.workflow.save()

        app_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        job_executables_dir = os.path.join(app_root_dir, 'job_executables')
        user_ws = app.get_user_workspace(self.user).path

        # Creating Condo Workflow Job Node
        prepare_modpath_job = CondorWorkflowJobNode(
            name='prepare_modpath_job',
            workflow=self.workflow,
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=[
                os.path.join(job_executables_dir, 'modpath_executable.py'),
                self.db_dir
            ],
        )

        # Setting appropriate arguments for the prepare_modpath executable
        prepare_modpath_job.set_attribute('executable', 'modpath_executable.py')
        prepare_modpath_job.set_attribute('arguments', (
            self.session_id,
            self.workflow.id,
            user_ws,
            self.modflow_exe,
            self.modpath_exe,
            'modpath7',
            '{}_{}'.format(self.app_package, self.database_id),
            self.nam_file,
            self.srid,
            self.xll,
            self.yll,
            self.rotation,
            self.lon,
            self.lat,
            self.depth,
            '4326',
            'Depth',
        ))

        # Files to be transferred to condor machine
        input_archive_filename = os.path.basename(self.db_dir)
        prepare_modpath_job.set_attribute('transfer_input_files', ('../{0}'.format(input_archive_filename),))
        prepare_modpath_job.set_attribute('transfer_output_files', ('flow_path.json',))
        prepare_modpath_job.save()

    def run_job(self):
        """
        Executes the prepared job.
        """
        resource_db_session = None

        try:
            self.prepare()
            self.workflow.execute()
        finally:
            resource_db_session and resource_db_session.close()
