"""
********************************************************************************
* Name: modify_modflow_model.py
* Author: ckrewson
* Created On: February 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
import logging
import json
from tethys_gizmos.gizmo_options import TextInput, SelectInput
from tethysext.atcore.exceptions import ModelDatabaseInitializationError
from tethysext.atcore.controllers.app_users import ModifyResource
from tethysext.atcore.services.model_file_database import ModelFileDatabase
from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager

from tethysapp.modflow.app import Modflow as app
from tethysapp.modflow.condor_workflows.project_upload import ProjectUploadWorkflow


__all__ = ['ModifyModflowModel']
log = logging.getLogger('modflow')


class ModifyModflowModel(ModifyResource):
    """
    Controller that handles the new and edit pages for Modflow model resources.
    """
    # Srid field options
    include_srid = True
    srid_required = True
    srid_default = ""
    srid_error = "Spatial reference is required."

    # File upload options
    include_file_upload = True
    file_upload_required = True
    file_upload_multiple = False
    file_upload_accept = ".zip"
    file_upload_label = "Modflow Files"
    file_upload_help = "Upload an archive containing the Modflow model input files."
    file_upload_error = "Must provide file(s)."

    template_name = 'modflow/app_users/modflow_modify_resource.html'

    def handle_resource_finished_processing(self, session, request, request_app_user, resource, editing):
        """
        Hook to allow for post processing after the resource has finished being created or updated.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            resource(Resource): The resource being edited or newly created.
            editing(bool): True if editing, False if creating a new resource.
        """

        # Only do the following if creating a new project
        if not editing:
            # get additional database fields for resource
            post_params = request.POST
            length_unit = post_params.get('lenunit', "L")
            time_unit = post_params.get('timeunit', "T")
            xll = post_params.get('xll', "")
            yll = post_params.get('yll', "")
            rotation = post_params.get('rotation', "")
            publication = post_params.get('publication', '')
            publication_link = post_params.get('publication_link', '')
            model_version = post_params.get('model-version', "")
            srid = resource.get_attribute('srid')
            valid = True

            # TODO: set gizmo errors if valid is false
            # Validate
            if not xll:
                valid = False

            if not yll:
                valid = False

            if not model_version:
                valid = False

            if valid:
                # Create a new model file database
                model_db = ModelFileDatabase(app=app)
                model_db_success = model_db.initialize()

                # Initialize Model File database
                if not model_db_success:
                    raise ModelDatabaseInitializationError(
                        'An error occurred while trying to initialize a model database.'
                    )

                # Add additional database fields to resource
                resource.set_attribute('xll', float(xll))
                resource.set_attribute('yll', float(yll))
                resource.set_attribute('rotation', float(rotation))
                resource.set_attribute('publication', publication)
                resource.set_attribute('publication_link', publication_link)

                # Keep the name to model_units for now to avoid breaking the code.
                resource.set_attribute('model_units', length_unit)
                resource.set_attribute('time_unit', time_unit)
                resource.set_attribute('model_version', model_version)
                resource.set_attribute('database_id', model_db.get_id())

                # Using file handle upload and adding it to the model file connection
                model_db.model_db_connection.add_zip_file(resource.get_attribute('files')[0])

                # Define additional job parameters
                gs_engine = app.get_spatial_dataset_service(app.GEOSERVER_NAME, as_engine=True)

                # Get model_extents from flopy
                spatial_manager = ModflowSpatialManager(gs_engine, model_db.model_db_connection, model_version)
                model_extents = spatial_manager.create_extent_for_project(xll, yll, rotation, srid)
                resource.set_attribute('model_extents', json.dumps(model_extents))

                geoserver_layers, geoserver_groups = spatial_manager.upload_all_layer_names_to_db(length_unit,
                                                                                                  time_unit)
                resource.set_attribute('geoserver_layers', json.dumps(geoserver_layers))
                resource.set_attribute('geoserver_groups', json.dumps(geoserver_groups))

                # Get model layer and number of stress periods
                number_layer = spatial_manager.get_number_layer()
                number_stress_period = spatial_manager.get_number_stress_period()

                resource.set_attribute('nlay', number_layer)
                resource.set_attribute('nper', number_stress_period)
                resource.set_attribute('max_stress_period', ModflowSpatialManager.MAX_STRESS_PERIOD)
                # Save new project
                session.commit()

                # Prepare condor job for processing file upload
                user_workspace = app.get_user_workspace(request.user)
                user_workspace_path = user_workspace.path
                workspace_id = resource.get_attribute('database_id')
                job_path = os.path.join(user_workspace_path, workspace_id)

                # Create job directory if it doesn't exist already
                if not os.path.exists(job_path):
                    os.makedirs(job_path)

                # Create the condor job and submit
                job = ProjectUploadWorkflow(
                    user=request.user,
                    workspace=job_path,
                    workflow_name=resource.name,
                    input_archive_path=model_db.directory,
                    xll=xll,
                    yll=yll,
                    rotation=rotation,
                    model_units=length_unit.lower(),
                    model_version=model_version,
                    srid=srid,
                    resource_db_url=app.get_persistent_store_database(app.DATABASE_NAME, as_url=True),
                    resource_id=str(resource.id),
                    scenario_id=1,
                    model_db=model_db,
                    gs_engine=gs_engine,
                    app_package=app.package,
                )
                job.run_job()
                log.info('PROJECT UPLOAD job submitted to HTCondor')
            else:
                raise Exception("more data needed")

    def get_context(self, context):
        """
        Hook to add to context.

        Args:
            context(dict): context for controller.

        Returns:
            Updated context with additional gizmos needed for the modflow model resource
        """

        xll_input_error = ""
        yll_input_error = ""
        rotation_input_error = ""
        model_version_select_error = ""
        # Define form
        length_unit = SelectInput(
                display_text='Length Unit of the Model',
                name='lenunit',
                multiple=False,
                initial='Feet',
                options=[('Feet', 'Feet'), ('Meters', 'Meters')],
            )

        # Define form
        time_unit = TextInput(
            display_text='Time Unit of the Model',
            name='timeunit',
            placeholder='',
            initial='Day',
        )
        # Define form
        publication = TextInput(
            display_text='Publication',
            name='publication',
            placeholder='',
            initial='',
        )

        # Define form
        publication_link = TextInput(
            display_text='Model Publication Link',
            name='publication_link',
            placeholder='',
            initial='',
        )

        # Define form
        xll_input = TextInput(
            display_text='Lower Left X Model Coordinate',
            name='xll',
            placeholder='',
            initial='',
            error=xll_input_error
        )

        yll_input = TextInput(
            display_text='Lower Left Y Model Coordinate',
            name='yll',
            placeholder='',
            initial='',
            error=yll_input_error
        )

        rotation = TextInput(
            display_text='The counter-clockwise rotation (in degrees) of the grid',
            name='rotation',
            placeholder='',
            initial='0',
            error=rotation_input_error,
        )

        model_version_select = SelectInput(
                display_text='Model Version',
                name='model-version',
                multiple=False,
                initial='mfnwt',
                options=[('mfnwt', 'mfnwt'),
                         ('mf2000', 'mf2000'),
                         ('mf2005', 'mf2005'),
                         ('modflow6', 'modflow6'),
                         ('mflgr', 'mflgr'),
                         ],
                error=model_version_select_error
            )

        context.update({
            'length_unit': length_unit,
            'time_unit': time_unit,
            'xll_input': xll_input,
            'yll_input': yll_input,
            'rotation': rotation,
            'model_version_select': model_version_select,
            'publication': publication,
            'publication_link': publication_link,
        })

        return context
