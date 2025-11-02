from setuptools import find_packages, setup
import os
from glob import glob


package_name = 'time_travelling'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nek1t',
    maintainer_email='Mr.Nikita2912@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'turtle_tf2_broadcaster = time_travelling.time_travel_broad:main',
            'time_traveller = time_travelling.time_traveller:main',
            
        ],
    },
)
