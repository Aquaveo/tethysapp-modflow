"""
********************************************************************************
* Name: organization.py
* Author: nswain
* Created On: May 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysapp.modflow.services.licenses import ModflowLicenses
from tethysext.atcore.models.app_users import Organization

__all__ = ['ModflowOrganization']


class ModflowOrganization(Organization):
    """
    Customized Organization model for Modflow.
    """
    TYPE = 'modflow-organization'
    LICENSES = ModflowLicenses()

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }
