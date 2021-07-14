"""
********************************************************************************
* Name: drawdown_workflow
* Author: ckrewson & thoang
* Created On: March 11, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
from tethys_sdk.jobs import CondorWorkflowJobNode
from tethysapp.modflow.app import Modflow as app
from tethys_sdk.compute import get_scheduler
from tethysapp.modflow.models.app_users.settings import AppSettings


class DrawdownWorkflow(object):
    """
    Class Based Controller for pump impact tool
    """
    WORKFLOW_ID = 'drawdown'

    def __init__(self, user, workspace, session_id, xll, yll, rotation, db_dir, model_units, model_version, modflow_exe,
                 nam_file, hds_file, wel_file, srid, resource_id, database_id, app_package, contour_levels,
                 export_layer_string, export_sp_string):
        """
        Constructor.

        Args:
            user(Django User): Django User
            workspace(str): 'path/to/user/workspace/session_id'
            session_id(str): Django session ID
            xll(float): lower left x coordinate for model
            yll(float): lower left y coordinate for model
            db_dir(str): path to model file database directory
            model_units(str): model units (feet or meters)
            model_version(str): modflow version for this model (i.e mfnwt, mf2000, mf2005, ect)
            modflow_exe(str): path to modflow executable
            nam_file(str): .nam file name
            hds_file(str): .hds file name
            wel_file(str): .wel file name if exists
            srid(str): srid
            resource_id (str): Resource ID
            database_id (str): Database ID for the given resource
            app_package(str): app package for the App (i.e modflow).
            layer: layer which results are analyzed.
        """  # noqa: E501

        self.user = user
        self.workspace = workspace
        self.session_id = session_id
        self.job_name = 'drawdown'
        self.safe_job_name = ''.join(s for s in self.job_name if s.isalnum())  #: Safe name with only A-Z 0-9
        self.xll = xll
        self.yll = yll
        self.rotation = rotation
        self.db_dir = db_dir
        self.model_units = model_units
        self.model_version = model_version
        self.modflow_exe = modflow_exe
        self.nam_file = nam_file
        self.hds_file = hds_file
        self.wel_file = wel_file
        self.srid = srid
        self.resource_id = resource_id
        self.database_id = database_id
        self.app_package = app_package
        self.contour_levels = contour_levels
        self.export_layer_string = export_layer_string
        self.export_sp_string = export_sp_string
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

        # Creating Condo Workflow Job Node
        prepare_drawdown_job = CondorWorkflowJobNode(
            name='drawdown_job',
            workflow=self.workflow,
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=[
                os.path.join(job_executables_dir, 'drawdown_executable.py'),
                self.db_dir
            ],
            attributes=dict(
                executable='drawdown_executable.py',
            )
        )

        if not self.contour_levels:
            # Setting appropriate arguments for the prepare_drawdown executable
            session = None
            try:
                create_session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
                session = create_session()
                drawdown_contour_level_name = 'drawdown_contour_level'
                drawdown_row = session.query(AppSettings).filter(AppSettings.name == drawdown_contour_level_name)\
                    .first()
                if drawdown_row.value.strip():
                    self.contour_levels = drawdown_row.value
                else:
                    self.contour_levels = "1/5/10/15"
            finally:
                session and session.close()

        self.contour_levels = self.contour_levels.replace(" ", "").replace(",", "/")

        prepare_drawdown_job.set_attribute('arguments', (
            self.modflow_exe,
            '{}_{}'.format(self.app_package, self.database_id),
            self.nam_file,
            self.hds_file,
            self.wel_file,
            self.srid,
            self.xll,
            self.yll,
            self.rotation,
            '4326',
            self.contour_levels,
            self.export_layer_string,
            self.export_sp_string,
        ))

        # Files to be transferred to condor machine
        input_archive_filename = os.path.basename(self.db_dir)
        prepare_drawdown_job.set_attribute('transfer_input_files', ('../{0}'.format(input_archive_filename),))
        prepare_drawdown_job.save()

        self.workflow.save()

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
