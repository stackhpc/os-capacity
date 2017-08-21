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

import argparse
import sys

from keystoneauth1 import loading as ks_loading

from keystoneauth1.identity import v3
from keystoneclient.v3 import client


def list_rps(argv):
    parser = argparse.ArgumentParser('os-capacity')
    ks_loading.register_session_argparse_arguments(parser)
    ks_loading.register_auth_argparse_arguments(parser, argv)

    (args, args_list) = parser.parse_known_args(argv)

    auth = ks_loading.load_auth_from_argparse_arguments(args)
    client = ks_loading.load_session_from_argparse_arguments(args, auth=auth)

    ks_filter = {'service_type': 'placement',
                 'region_name': 'RegionOne',
                 'interface': 'public'}
    url = "/resource_providers" 
    print client.get(
            url,
            endpoint_filter=ks_filter).json()

if __name__ == "__main__":
    list_rps(sys.argv)
