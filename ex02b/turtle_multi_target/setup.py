from setuptools import find_packages, setup

package_name = 'turtle_multi_target'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/turtle_launch.py']),

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
            'target_switcher = turtle_multi_target.target_switcher:main',
            'turtle_broadcaster = turtle_multi_target.turtle_broadcaster:main',
            'turtle_controller = turtle_multi_target.turtle_controller:main'
        ],
    },
)
