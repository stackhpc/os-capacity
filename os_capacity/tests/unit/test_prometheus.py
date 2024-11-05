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

import unittest

from os_capacity import prometheus


class FakeFlavor:
    def __init__(self, id, name, vcpus, ram, disk, ephemeral, extra_specs):
        self.id = id
        self.name = name
        self.vcpus = vcpus
        self.ram = ram
        self.disk = disk
        self.ephemeral = ephemeral
        self.extra_specs = extra_specs


class TestFlavor(unittest.TestCase):
    def test_get_placement_request(self):
        flavor = FakeFlavor(
            "fake_id", "fake_name", 8, 2048, 30, 0, {"hw:cpu_policy": "dedicated"}
        )
        resources, traits = prometheus.get_placement_request(flavor)

        self.assertEqual({"PCPU": 8, "MEMORY_MB": 2048, "DISK_GB": 30}, resources)
        self.assertEqual([], traits)
