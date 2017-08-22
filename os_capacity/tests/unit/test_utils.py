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

        expected_flavors = [('d0e9df0c-34a3-4283-9547-d873e4e86a41',
            'compute-GPU', 8, 2048, 30)]
        self.assertEqual(expected_flavors, result)

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

    @mock.patch.object(utils, '_get_allocations')
    @mock.patch.object(utils, '_get_inventories')
    @mock.patch.object(utils, 'get_resource_providers')
    def test_get_all_inventories_and_usage(self, mock_grp, mock_gi, mock_a):
        fake_rps = [('uuid1', 'name1'), ('uuid2', 'name2'),
                    ('uuid3', 'name3')]
        mock_grp.return_value = fake_rps
        fake_inventories = {
            'uuid1': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
            'uuid2': {},
            'uuid3': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
        }
        mock_gi.return_value = fake_inventories
        fake_allocations = {
            'uuid1': {"server-uuid1": {
                'DISK_GB': 371,'MEMORY_MB': 131072, 'VCPU': 64}},
            'uuid3': {},
        }
        mock_a.return_value = fake_allocations

        result = list(utils.get_all_inventories_and_usage(mock.Mock()))

        self.assertEqual([
                ('uuid1', 'name1', 30, 20, 10, True),
                ('uuid2', 'name2', None, None, None, False),
                ('uuid3', 'name3', 30, 20, 10, False),
            ], result)

    def test_group_inventories(self):
        fake_all_inventories = [
            ('uuid1', 'name1', 30, 20, 10),
            ('uuid2', 'name2', 0, 0, 0),
            ('uuid3', 'name3', 30, 20, 10),
        ]
        fake_flavors = [
            ('uuid1', 'test1', 30, 20, 10),
            ('uuid2', 'test2', 30, 20, 10),
            ('uuid3', 'test3', 8, 2048, 30),
        ]

        result = list(utils.group_all_inventories(
            fake_all_inventories, fake_flavors))

        self.assertEquals(2, len(result))
        self.assertEquals([
            ('VCPU:30,MEMORY_MB:20,DISK_GB:10', 2, "test1, test2"),
            ('VCPU:0,MEMORY_MB:0,DISK_GB:0', 1, '')], result)

    def test_get_all_allocations(self):
        fake_rps = [('uuid1', 'name1')]
        fake_allocations = {
            'allocations': {
                'c1d70ef7-f26b-4147-bcf9-0fd91ddaf8f6': {
                    'resources': {
                        'DISK_GB': 371,'MEMORY_MB': 131072, 'VCPU': 64}
                },
            'resource_provider_generation': 43}
        }
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fake_allocations
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        result = utils._get_allocations(app, fake_rps)

        app.placement_client.get.assert_called_once_with(
            "/resource_providers/uuid1/allocations")
        self.assertEqual({'uuid1': fake_allocations['allocations']}, result)
