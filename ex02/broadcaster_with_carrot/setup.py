from setuptools import find_packages, setup
import os
from glob import glob


package_name = 'broadcaster_with_carrot'

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
            'carrot_frame_broadcaster = broadcaster_with_carrot.carrot_frame:main',
            'turtle1_broadcaster = broadcaster_with_carrot.turtle1_broadcaster:main',
            'turtle1_listener = broadcaster_with_carrot.turtle1_listener:main',
            
        ],
    },
)
