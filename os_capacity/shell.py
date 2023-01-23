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

import sys

from cliff.app import App
from cliff.commandmanager import CommandManager
import os_client_config

import openstack

def get_cloud_config():
    # TODO(johngarbutt) consider passing in argument parser
    return os_client_config.get_config()


def get_client(cloud_config, service_type):
    return cloud_config.get_session_client(service_type)


class CapacityApp(App):

    def __init__(self):
        super(CapacityApp, self).__init__(
            description='OS-Capacity (StackHPC) Command Line Interface (CLI)',
            version='0.1',
            command_manager=CommandManager('os_capacity.commands'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

        conn = openstack.connect()
        self.connection = conn
        self.compute_client = conn.compute
        self.placement_client = conn.placement
        self.identity_client = conn.identity

        self.LOG.debug('setup Keystone API REST clients')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    myapp = CapacityApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
