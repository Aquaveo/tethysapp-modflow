import logging
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from tethys_apps.models import TethysApp
from tethysapp.modflow.models.app_users.settings import AppSettings
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.services.app_users.roles import Roles
from tethys_apps.exceptions import TethysAppSettingNotAssigned
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager

log = logging.getLogger('tethys.' + __name__)


@receiver(post_save, sender=User, dispatch_uid='modflow.signal')
def assign_organization(sender, instance, created, **kwargs):
    from tethysapp.modflow.app import Modflow as app

    if created:
        session = None
        try:
            create_session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
            if create_session:
                session = create_session()
                # Check to see if username exists
                user_row = session.query(AppUser).filter(AppUser.username == instance.username).count()

                if not user_row:
                    default_org_row = session.query(AppSettings).filter(AppSettings.name == 'default_organization') \
                        .first()
                    # If we find default organization, we will assign the user to this one
                    if default_org_row:
                        assigned_organization_id = default_org_row.value
                        assigned_organization = session.query(Organization) \
                            .filter(Organization.id == assigned_organization_id).first()
                    # Otherwise, we'll assign the user to the first organization.
                    else:
                        assigned_organization = session.query(Organization).first()

                    if assigned_organization:
                        # By default, the role is organization user.
                        assigned_role = Roles.ORG_USER

                        new_app_user = AppUser(
                            username=instance.username,
                            role=assigned_role,
                        )
                        # Get permissions manager
                        permissions_manager = AppPermissionsManager(app.package)

                        # Add user to selected organizations and assign custom_permissions
                        new_app_user.organizations.append(assigned_organization)
                        permissions_manager.assign_user_permission(
                            new_app_user,
                            new_app_user.role,
                            assigned_organization.license
                        )
                        session.add(new_app_user)

                session.commit()
        except (User.DoesNotExist, TethysApp.DoesNotExist) as e:
            log.warning(f'User or TethysApp models not found: {str(e)}')
        except TethysAppSettingNotAssigned as e:
            log.warning(f'PersistentStore has not been assigned. Error message: {str(e)}')
        finally:
            session and session.close()
