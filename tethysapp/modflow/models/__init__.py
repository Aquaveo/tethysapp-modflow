from tethysext.atcore.models.app_users import initialize_app_users_db


def init_primary_db(engine, first_time):
    """
    Initializer for the primary database.
    """
    # Initialize app users tables
    initialize_app_users_db(engine, first_time)
