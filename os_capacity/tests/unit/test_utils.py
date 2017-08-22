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

import mock
import unittest

from os_capacity import utils


class TestUtils(unittest.TestCase):

    def test_get_capacity(self):
        result = utils.get_capacity()
        self.assertEqual(1, len(result))
        self.assertEqual(2, len(result[0]))
        self.assertEqual("foo", result[0]["flavor"])
        self.assertEqual(1, result[0]["count"])

    def test_get_flavors(self):
        fake_flavor = {
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
        fake_response = mock.MagicMock()
        fake_response.json.return_value = {'flavors': [fake_flavor]}
        app = mock.MagicMock()
        app.compute_client.get.return_value = fake_response

        result = utils.get_flavors(app)

        self.assertEqual(1, len(result))
        flavor = result[0]
        self.assertEqual(5, len(flavor))
        self.assertEqual(fake_flavor['id'], flavor[0])
        self.assertEqual(fake_flavor['name'], flavor[1])
        self.assertEqual(fake_flavor['vcpus'], flavor[2])
        self.assertEqual(fake_flavor['ram'], flavor[3])
        self.assertEqual(fake_flavor['disk'], flavor[4])
