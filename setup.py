# Copyright (c) 2017 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python

from setuptools import setup, find_packages


PROJECT = 'os_capacity'
VERSION = '0.1'

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='OpenStack capacity tooling',
    long_description=long_description,

    author='StackHPC',
    author_email='john.garbutt@stackhpc.com',

    url='https://github.com/stackhpc/os-capacity',
    download_url='https://github.com/stackhpc/os-capacity/tarball/master',

    provides=[],
    install_requires=open('requirements.txt', 'rt').read().splitlines(),

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'os-capacity = os_capacity.cmd.os_capacity:main',
        ],
        'os_capacity.cli': [
            'capacity_get = os_capacity.cli.commands:CapacityGet',
        ],
    },
)
