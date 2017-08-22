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

    def test_get_resource_providers(self):
        fake_rp = {
            'generation': 6,
            'name': 'name1',
            'uuid': '97585d53-67a6-4e9d-9fe7-cd75b331b17b',
            'links': [
                {'href': '/resource_providers'
                         '/97585d53-67a6-4e9d-9fe7-cd75b331b17c',
                 'rel': 'self'},
                {'href': '/resource_providers'
                         '/97585d53-67a6-4e9d-9fe7-cd75b331b17c/aggregates',
                 'rel': 'aggregates'},
                {'href': '/resource_providers'
                         '/97585d53-67a6-4e9d-9fe7-cd75b331b17c/inventories',
                 'rel': 'inventories'},
                {'href': '/resource_providers'
                         '/97585d53-67a6-4e9d-9fe7-cd75b331b17c/usages',
                 'rel': 'usages'}
            ]
        }
        fake_response = mock.MagicMock()
        fake_response.json.return_value = {'resource_providers': [fake_rp]}
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        result = utils.get_resource_providers(app)

        app.placement_client.get.assert_called_once_with("/resource_providers")
        self.assertEqual([(fake_rp['uuid'], 'name1')], result)

    def test_get_inventories(self):
        fake_rps = [('uuid1', 'name1'), ('uuid2', 'name2')]
        fake_ironic_inventories = {'inventories': {
            'DISK_GB': {
                'allocation_ratio': 1.0,
                'max_unit': 10,
                'min_unit': 1,
                'reserved': 0,
                'step_size': 1,
                'total': 10},
            'MEMORY_MB': {'max_unit': 20},
            'VCPU': {'max_unit': 30},
        }}
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fake_ironic_inventories
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        result = utils._get_inventories(app, fake_rps)

        app.placement_client.get.assert_called_with(
            "/resource_providers/uuid2/inventories")
        self.assertEqual({
                'uuid1': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
                'uuid2': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
            }, result)

    @mock.patch.object(utils, '_get_inventories')
    @mock.patch.object(utils, 'get_resource_providers')
    def test_get_all_inventories(self, mock_grp, mock_gi):
        fake_rps = [('uuid1', 'name1'), ('uuid2', 'name2')]
        mock_grp.return_value = fake_rps
        fake_inventories = {
            'uuid1': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
            'uuid2': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 32}}
        mock_gi.return_value = fake_inventories

        result = list(utils.get_all_inventories(mock.Mock()))

        self.assertEqual([
                ('uuid1', 'name1', 10, 20, 30),
                ('uuid2', 'name2', 10, 20, 32)
            ], result)
