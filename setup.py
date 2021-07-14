from setuptools import setup, find_namespace_packages
from tethys_apps.app_installation import find_resource_files

# -- Apps Definition -- #
app_package = 'modflow'
release_package = 'tethysapp-' + app_package

# -- Get Resource File -- #
resource_files = find_resource_files('tethysapp/modflow/templates', 'tethysapp/modflow')
resource_files += find_resource_files('tethysapp/modflow/public', 'tethysapp/modflow')
resource_files += find_resource_files('tethysapp/modflow/workspaces', 'tethysapp/modflow')

setup(
    name=release_package,
    version='0.0.1',
    description='Application for evaluating pumping location and pumping rates effects on aquifers',
    long_description='',
    keywords='',
    author='Corey Krewson, Tran Hoang, Nathan Swain',
    author_email='nswain@aquaveo.com',
    url='',
    license='',
    packages=find_namespace_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    package_data={'': resource_files},
    zip_safe=False,
    install_requires=[],
    test_suite='tethys_apps.tethysapp.modflow.tests.unit_tests',
    entry_points={
        'console_scripts': ['modflow=tethysapp.modflow.cli:modflow_command'],
    },
)
