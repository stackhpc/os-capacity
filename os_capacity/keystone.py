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

import pprint

import os_client_config


def get_cloud_config():
    # TODO(johngarbutt) consider passing in argument parser
    return os_client_config.get_config()


def get_client(cloud_config, service_type):
    return cloud_config.get_session_client(service_type)


def print_flavors(client):
    url_list_providers = "/flavors"
    response = client.get(url_list_providers).json()
    print
    print "Flavors:"
    print
    pprint.pprint(response['flavors'])


def print_rps(client):
    url_list_providers = "/resource_providers"
    response = client.get(url_list_providers).json()
    print
    print "Resource Providers:"
    print
    pprint.pprint(response['resource_providers'])

    resources = "VCPU:64"
    version = "1.10"
    headers = {
        'OpenStack-API-Version': 'placement %s' % version
    }
    candidates = client.get(
        "/allocation_candidates?resources=%s" % resources,
        headers=headers).json()
    print
    print "Candidates:"
    print
    pprint.pprint(candidates)


if __name__ == "__main__":
    cloud_config = get_cloud_config()

    compute_client = get_client(cloud_config, "compute")
    print_flavors(compute_client)

    placement_client = get_client(cloud_config, "placement")
    print_rps(placement_client)
