from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting, PersistentStoreConnectionSetting, \
    SpatialDatasetServiceSetting, CustomSetting
from tethys_sdk.permissions import Permission
import tethysapp.modflow.signals  # noqa


class Modflow(TethysAppBase):
    """
    Tethys app class for Modflow.
    """

    name = 'Groundwater Model Simulations'
    index = 'modflow:home'
    icon = 'modflow/images/icon-gms-tethys-170.png'
    package = 'modflow'
    root_url = 'modflow'
    color = '#BA0C2F'
    description = 'Application for evaluating pumping location and pumping rates effects on aquifers'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    # Services
    SCHEDULER_NAME = 'remote_cluster'
    GEOSERVER_NAME = 'primary_geoserver'
    DATABASE_NAME = 'primary_db'
    MODEL_DB_CON_01 = 'model_db_1'

    BASE_SCENARIO_ID = 1

    def custom_settings(self):
        """
        Define custom settings.
        """
        custom_settings = (
            CustomSetting(
                name='bing_api_key',
                type=CustomSetting.TYPE_STRING,
                description='API key for BING basemap service.',
                required=False
            ),
            CustomSetting(
                name='minx_extent',
                type=CustomSetting.TYPE_STRING,
                description='Min X Extent for Model Selection Map View',
                required=True
            ),
            CustomSetting(
                name='miny_extent',
                type=CustomSetting.TYPE_STRING,
                description='Min Y Extent for Model Selection Map View',
                required=True
            ),
            CustomSetting(
                name='maxx_extent',
                type=CustomSetting.TYPE_STRING,
                description='Max X Extent for Model Selection Map View',
                required=True
            ),
            CustomSetting(
                name='maxy_extent',
                type=CustomSetting.TYPE_STRING,
                description='Max Y Extent for Model Selection Map View',
                required=True
            ),
            CustomSetting(
                name='custom_base_maps',
                type=CustomSetting.TYPE_STRING,
                description='Comma separated urls for basemap services (ex. name1:url1, name2:url2)',
                required=False
            ),
        )

        return custom_settings

    def url_maps(self):
        """
        Add controllers
        """
        from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
        from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager
        from tethysext.atcore.urls import app_users, spatial_reference
        from tethysapp.modflow.models.app_users import ModflowOrganization
        from tethysapp.modflow.services.map_manager import ModflowMapManager
        from tethysapp.modflow.controllers.resources import ModifyModflowModel
        from tethysapp.modflow.controllers.map_view.modflow_model_map_view import ModflowModelMapView

        UrlMap = url_map_maker(self.root_url)

        # Get the urls for the app_users extension
        url_maps = []

        app_users_urls = app_users.urls(
            url_map_maker=UrlMap,
            app=self,
            persistent_store_name=self.DATABASE_NAME,
            base_template='modflow/base.html',
            custom_models=(
                ModflowModelResource,
                ModflowOrganization
            ),
            custom_controllers=(
                ModifyModflowModel,
            ),
        )
        url_maps.extend(app_users_urls)

        spatial_reference_urls = spatial_reference.urls(
            url_map_maker=UrlMap,
            app=self,
            persistent_store_name=self.DATABASE_NAME
        )
        url_maps.extend(spatial_reference_urls)

        url_maps.extend((
            UrlMap(
                name='home',
                url='modflow',
                controller=ModflowModelMapView.as_controller(
                    _app=self,
                    _persistent_store_name=self.DATABASE_NAME,
                    geoserver_name=self.GEOSERVER_NAME,
                    _Organization=ModflowOrganization,
                    _Resource=ModflowModelResource,
                    _SpatialManager=ModflowSpatialManager,
                    _MapManager=ModflowMapManager
                ),
                regex=['[0-9A-Za-z-_.]+', '[0-9A-Za-z-_.{}]+']
            ),
            UrlMap(
                name='model_view',
                url='modflow/{resource_id}/map',
                controller=ModflowModelMapView.as_controller(
                    _app=self,
                    _persistent_store_name=self.DATABASE_NAME,
                    geoserver_name=self.GEOSERVER_NAME,
                    _Organization=ModflowOrganization,
                    _Resource=ModflowModelResource,
                    _SpatialManager=ModflowSpatialManager,
                    _MapManager=ModflowMapManager
                ),
                regex=['[0-9A-Za-z-_.]+', '[0-9A-Za-z-_.{}]+']
            ),
            UrlMap(
                name='modpath',
                url='modflow/modpath',
                controller='modflow.controllers.executables.modpath.modpath'
            ),
            UrlMap(
                name='get-flow-path-json',
                url='modflow/get-flow-path-json',
                controller='modflow.controllers.executables.modpath.get_flow_path_json'
            ),
            UrlMap(
                name='pump-impact',
                url='modflow/pump-impact',
                controller='modflow.controllers.executables.pump_impact.pump_impact'
            ),
            UrlMap(
                name='get-pump-impact-json',
                url='modflow/get-pump-impact-json',
                controller='modflow.controllers.executables.pump_impact.get_pump_impact_json'
            ),
            UrlMap(
                name='check-job-status',
                url='modflow/check-job-status',
                controller='modflow.controllers.executables.job_status.check_status'
            ),
            UrlMap(
                name='check-point-status',
                url='modflow/check-point-status',
                controller='modflow.controllers.rest.map.check_point_status'
            ),
            UrlMap(
                name='check-well-depth',
                url='modflow/check-well-depth',
                controller='modflow.controllers.rest.map.check_well_depth'
            ),
            UrlMap(
                name='pump-schedule-data',
                url='modflow/pump-schedule-data',
                controller='modflow.controllers.rest.map.pump_schedule_data'
            ),
            UrlMap(
                name='update-help-modal-status',
                url='modflow/update-help-modal-status',
                controller='modflow.controllers.rest.map.update_help_modal_status'
            ),
            UrlMap(
                name='settings',
                url='settings',
                controller='modflow.controllers.manage.modflow_settings.modflow_settings'
            ),
        ))

        return url_maps

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name=self.DATABASE_NAME,
                description='Primary database for Modflow.',
                initializer='modflow.models.init_primary_db',
                required=True,
                spatial=True
            ),
            PersistentStoreConnectionSetting(
                name=self.MODEL_DB_CON_01,
                description='First node of model database server pool.',
                required=True
            ),
        )

        return ps_settings

    def spatial_dataset_service_settings(self):
        """
        Example spatial_dataset_service_settings method.
        """
        sds_settings = (
            SpatialDatasetServiceSetting(
                name=self.GEOSERVER_NAME,
                description='spatial dataset service for app to use',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

        return sds_settings

    def permissions(self):
        """
        Example permissions method.
        """
        # Viewer Permissions
        admin_user = Permission(
            name='admin_user',
            description='Admin User'
        )

        from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
        from tethysext.atcore.permissions.app_users import PermissionsGenerator

        # Generate permissions for App Users
        permissions_manager = AppPermissionsManager(self.namespace)
        pg = PermissionsGenerator(permissions_manager)
        permissions = pg.generate()

        permissions.append(admin_user)

        return permissions
