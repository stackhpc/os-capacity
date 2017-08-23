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

FLAVOR = {
    'OS-FLV-DISABLED:disabled': False,
    'OS-FLV-EXT-DATA:ephemeral': 0,
    'disk': 30,
    'id': 'd0e9df0c-34a3-4283-9547-d873e4e86a41',
    'links': [
        {'href': 'http://example.com:8774/v2.1/flavors/'
                 'd0e9df0c-34a3-4283-9547-d873e4e86a41',
         'rel': 'self'},
        {'href': 'http://10.60.253.1:8774/flavors/'
                 'd0e9df0c-34a3-4283-9547-d873e4e86a41',
         'rel': 'bookmark'}],
    'name': 'compute-GPU',
    'os-flavor-access:is_public': True,
    'ram': 2048,
    'rxtx_factor': 1.0,
    'swap': '',
    'vcpus': 8,
}
FLAVOR_RESPONSE = {'flavors': [FLAVOR]}
