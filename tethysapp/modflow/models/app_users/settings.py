import uuid
from sqlalchemy import Column, String
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.models.app_users import AppUsersBase

__all__ = ['AppSettings']


class AppSettings(AppUsersBase):
    """
    Definition for the app_users_settings table. All app users are associated with django users.
    """
    __tablename__ = 'app_users_settings'
    __table_args__ = {'extend_existing': True}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String, nullable=True)
    value = Column(String, nullable=True)

    def __init__(self, name=name, description=description, value=value, *args, **kwargs):
        """
        Contstructor.
        """
        self.name = name
        self.description = description
        self.value = value
        # Call super class
        super(AppSettings, self).__init__(*args, **kwargs)
