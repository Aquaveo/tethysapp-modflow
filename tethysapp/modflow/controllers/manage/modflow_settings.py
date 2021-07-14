"""
********************************************************************************
* Name: account.py
* Author: nswain
* Created On: November 14, 2016
* Copyright: (c) Aquaveo 2016
* License:
********************************************************************************
"""
# Django
from django.shortcuts import render
# Tethys core
from tethys_sdk.permissions import has_permission, permission_required

from tethys_sdk.gizmos import TextInput, SelectInput
from tethysapp.modflow.models.app_users.settings import AppSettings
from tethysapp.modflow.app import Modflow as app
from tethysext.atcore.models.app_users import AppUser


@permission_required('has_app_admin_role')
def modflow_settings(request):

    session = None
    try:
        # Getting model attribute data from database
        Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
        session = Session()
        drawdown_contour_level_name = 'drawdown_contour_level'
        drawdown_contour_level_description = 'Drawdown Contour Levels - Comma separated list of drawdown ' \
                                             'contour levels. Up to 5 levels (ex: 1, 5, 10, 15)'
        std_minimum_change_name = 'std_minimum_change'
        std_minimum_change_description = "The minimum percent change in streamflow or leakage required for " \
                                         "a result to be shown in the results"

        default_organization_name = 'default_organization'
        default_organization_description = 'Default Organization which user will be associated to upon sign up'

        # Get organizations data
        request_app_user = AppUser.get_app_user_from_request(request, session)
        organization_options = request_app_user.get_organizations(session, request, as_options=True, cascade=True)

        # Initial Commit to check if we need to generate initial setting at the first time.
        initial_commit = False
        drawdown_row = session.query(AppSettings).filter(AppSettings.name == drawdown_contour_level_name).first()
        if drawdown_row:
            initial_drawdown = drawdown_row.value
        # Generate default settings
        else:
            initial_drawdown = ""
            insert_data = AppSettings(drawdown_contour_level_name, drawdown_contour_level_description, initial_drawdown)
            session.add(insert_data)
            initial_commit = True

        # Update database for std_minimum_change
        std_minimum_change_row = session.query(AppSettings).filter(AppSettings.name == std_minimum_change_name).first()

        if std_minimum_change_row:
            initial_std_min = std_minimum_change_row.value
        # Generate default settings
        else:
            initial_std_min = ""
            insert_data = AppSettings(std_minimum_change_name, std_minimum_change_description, initial_std_min)
            session.add(insert_data)
            initial_commit = True

        # Update database for selected_organization
        selected_organization = session.query(AppSettings).filter(AppSettings.name == 'default_organization').first()

        if selected_organization:
            initial_organization = selected_organization.value
        else:
            initial_organization = ""
            insert_data = AppSettings(default_organization_name, default_organization_description, initial_organization)
            session.add(insert_data)
            initial_commit = True

        if initial_commit:
            session.commit()

        if request.POST and 'modify-modflow-settings-save' in request.POST:
            drawdown_contour_level = request.POST.get(drawdown_contour_level_name)
            std_minimum_change = request.POST.get(std_minimum_change_name)
            selected_organization = request.POST.get(default_organization_name)

            initial_drawdown = drawdown_contour_level
            initial_std_min = std_minimum_change
            initial_organization = selected_organization

            # Update database for drawdown
            drawdown_row = session.query(AppSettings).filter(AppSettings.name == drawdown_contour_level_name).first()
            if drawdown_row:
                setattr(drawdown_row, "value", drawdown_contour_level)

            # Update database for std_minimum_change
            std_minium_change_row = session.query(AppSettings).\
                filter(AppSettings.name == std_minimum_change_name).first()

            if std_minium_change_row:
                setattr(std_minium_change_row, "value", std_minimum_change)

            # Update database for std_minimum_change
            default_organization_row = session.query(AppSettings).\
                filter(AppSettings.name == 'default_organization').first()
            if default_organization_row:
                setattr(default_organization_row, "value", selected_organization)

            session.commit()

        # Gizmo Input
        drawdown_contour_levels_input = TextInput(
            display_text=drawdown_contour_level_description,
            name=drawdown_contour_level_name,
            placeholder='',
            initial=initial_drawdown,
        )

        # std minimum input
        std_minimum_change_input = TextInput(
            display_text=std_minimum_change_description,
            name=std_minimum_change_name,
            placeholder='',
            initial=initial_std_min,
        )

        # Default Organization input
        organization_select = SelectInput(
            display_text=default_organization_description,
            name='default_organization',
            multiple=False,
            initial=initial_organization,
            options=organization_options,
        )
    finally:
        session and session.close()

    context = {"drawdown_contour_levels_input": drawdown_contour_levels_input,
               "std_minimum_change_input": std_minimum_change_input,
               "organization_select": organization_select,
               "show_resources_link": has_permission(request, 'view_resources'),
               "show_users_link": has_permission(request, 'modify_users'),
               "show_organizations_link": has_permission(request, 'view_organizations'),
               "is_app_admin": has_permission(request, 'has_app_admin_role')}

    return render(request, 'modflow/manage/modflow_settings.html', context)
