import pyproj
from tethysext.atcore.models.app_users.user_setting import UserSetting
from tethysext.atcore.models.app_users import AppUser
from tethysapp.modflow.app import Modflow as app


def transform(x, y, inprj, outprj):
    if "+" in inprj:
        inprj = pyproj.Proj(str(inprj), preserve_units=True)
    else:
        inprj = pyproj.Proj(init='epsg:' + str(inprj), preserve_units=True)

    if "+" in outprj:
        outprj = pyproj.Proj(str(outprj), preserve_units=True)
    else:
        outprj = pyproj.Proj(init='epsg:' + str(outprj), preserve_units=True)
    x, y = pyproj.transform(inprj, outprj, x, y)
    return x, y


def show_helper_status(request, page_name):
    session = None
    try:
        variable = 'show_helper_' + page_name

        # Get user
        create_session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
        session = create_session()
        current_setting = session.query(UserSetting).filter(AppUser.username == request.user.username).filter(
            UserSetting.key == variable).first()
        if current_setting:
            return current_setting.value == 'true'
        else:
            return True

    finally:
        session and session.close()
