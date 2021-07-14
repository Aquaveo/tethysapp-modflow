"""
********************************************************************************
* Name: stream_depletion_workflow
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


class RunAllToolsWorkflow(object):
    """
    Class Based Controller for pump impact tool
    """
    WORKFLOW_ID = 'run_all_tools'

    def __init__(self, user, workspace, session_id, xll, yll, rotation, db_dir, model_units, model_version, modflow_exe,
                 nam_file, wel_file, srid, resource_id, database_id, app_package, stream_package,
                 std_minimum_change, export_layer_string, export_sp_string, contour_levels):
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
            cbb_file(str): .cbb file name
            wel_file(str): .wel file name if exists
            srid(str): srid
            contour_levels(str): Drawdown Contour Levels - Comma separated list of drawdown contour levels. Up to
             5 levels(ex: 1, 5, 10, 15)
            resource_id (str): Resource ID
            database_id (str): Database ID for the given resource
            app_package(str): app package for the App (i.e modflow).
            stream_package(str): name of the flow package representing stream (i.e. STR, DRAINS)
        """  # noqa: E501

        self.user = user
        self.workspace = workspace
        self.session_id = session_id
        self.job_name = 'run_all_tools'
        self.safe_job_name = ''.join(s for s in self.job_name if s.isalnum())  #: Safe name with only A-Z 0-9
        self.xll = xll
        self.yll = yll
        self.rotation = rotation
        self.db_dir = db_dir
        self.model_units = model_units
        self.model_version = model_version
        self.modflow_exe = modflow_exe
        self.nam_file = nam_file
        self.wel_file = wel_file
        self.srid = srid
        self.resource_id = resource_id
        self.database_id = database_id
        self.app_package = app_package
        self.stream_package = stream_package
        self.std_minimum_change = std_minimum_change
        self.workflow = None
        self.export_layer_string = export_layer_string
        self.export_sp_string = export_sp_string
        self.contour_levels = contour_levels

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
        prepare_run_all_tools_job = CondorWorkflowJobNode(
            name='run_all_tools_job',
            workflow=self.workflow,
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=[
                os.path.join(job_executables_dir, 'run_all_tools_executable.py'),
                self.db_dir
            ],
            attributes=dict(
                executable='run_all_tools_executable.py',
            )
        )

        if not self.std_minimum_change:
            # Setting appropriate arguments for the prepare_run_all_tools executable
            session = None
            try:
                create_session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
                session = create_session()
                std_minimum_change_name = 'std_minimum_change'
                std_minimum_change_row = session.query(AppSettings).\
                    filter(AppSettings.name == std_minimum_change_name).first()
                if std_minimum_change_row:
                    self.std_minimum_change = std_minimum_change_row.value
            finally:
                session and session.close()

        if not self.export_layer_string:
            self.export_layer_string = '1'

        self.contour_levels = self.contour_levels.replace(" ", "").replace(",", "/")
        prepare_run_all_tools_job.set_attribute('arguments', (
            self.modflow_exe,
            '{}_{}'.format(self.app_package, self.database_id),
            self.nam_file,
            self.wel_file,
            self.srid,
            self.xll,
            self.yll,
            self.rotation,
            '4326',
            self.contour_levels,
            'Polygon',
            'All',
            'transformation_lookup.json',
            self.std_minimum_change,
            self.export_layer_string,
            self.export_sp_string,
            self.stream_package,
        ))

        # Files to be transferred to condor machine
        input_archive_filename = os.path.basename(self.db_dir)
        prepare_run_all_tools_job.set_attribute('transfer_input_files', ('../{0}'.format(input_archive_filename),))
        prepare_run_all_tools_job.save()

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
