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

RESOURCE_PROVIDER = {
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
RESOURCE_PROVIDER_RESPONSE = {'resource_providers': [RESOURCE_PROVIDER]}

INVENTORIES = {
    'DISK_GB': {
        'allocation_ratio': 1.0,
        'max_unit': 10,
        'min_unit': 1,
        'reserved': 0,
        'step_size': 1,
        'total': 10},
    'MEMORY_MB': {
        'max_unit': 20,
        'total': 20},
    'VCPU': {
        'max_unit': 30,
        'total': 30},
}
INVENTORIES_RESPONSE = {
    'inventories': INVENTORIES,
    'resource_provider_generation': 7,
}

ALLOCATIONS = {
    'consumer_uuid': {
        'resources': {
            'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30}
    }
}
ALLOCATIONS_RESPONSE = {
    'allocations': ALLOCATIONS,
    'resource_provider_generation': 42,
}

SERVER = {
    "OS-DCF:diskConfig": "AUTO",
    "OS-EXT-AZ:availability_zone": "nova",
    "OS-EXT-SRV-ATTR:host": "compute",
    "OS-EXT-SRV-ATTR:hostname": "new-server-test",
    "OS-EXT-SRV-ATTR:hypervisor_hostname": "fake-mini",
    "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
    "OS-EXT-SRV-ATTR:kernel_id": "",
    "OS-EXT-SRV-ATTR:launch_index": 0,
    "OS-EXT-SRV-ATTR:ramdisk_id": "",
    "OS-EXT-SRV-ATTR:reservation_id": "r-ov3q80zj",
    "OS-EXT-SRV-ATTR:root_device_name": "/dev/sda",
    "OS-EXT-SRV-ATTR:user_data": "",
    "OS-EXT-STS:power_state": 1,
    "OS-EXT-STS:task_state": None,
    "OS-EXT-STS:vm_state": "active",
    "OS-SRV-USG:launched_at": "2017-02-14T19:23:59.895661",
    "OS-SRV-USG:terminated_at": None,
    "accessIPv4": "1.2.3.4",
    "accessIPv6": "80fe::",
    "addresses": {
        "private": [
            {
                "OS-EXT-IPS-MAC:mac_addr": "aa:bb:cc:dd:ee:ff",
                "OS-EXT-IPS:type": "fixed",
                "addr": "192.168.0.3",
                "version": 4
            }
        ]
    },
    "config_drive": "",
    "created": "2017-02-14T19:23:58Z",
    "description": "fake description",
    "flavor": {
        "id": "7b46326c-ce48-4e43-8aca-4f5ca00d5f37",
        "ephemeral": 0,
        "extra_specs": {
            "hw:cpu_model": "SandyBridge",
            "hw:mem_page_size": "2048",
            "hw:cpu_policy": "dedicated"
        },
        "original_name": "m1.tiny.specs",
        "ram": 512,
        "swap": 0,
        "vcpus": 1
    },
    "hostId": "2091634baaccdc4c5a1d57069c833e402921df696b7f970791b12ec6",
    "host_status": "UP",
    "id": "9168b536-cd40-4630-b43f-b259807c6e87",
    "image": {
        "id": "70a599e0-31e7-49b7-b260-868f441e862b",
        "links": [
            {
                "href": "http://openstack.example.com"
                        "/images/70a599e0-31e7-49b7-b260-868f441e862b",
                "rel": "bookmark"
            }
        ]
    },
    "key_name": None,
    "links": [
        {
            "href": "http://openstack.example.com/v2.1/servers"
                    "/9168b536-cd40-4630-b43f-b259807c6e87",
            "rel": "self"
        },
        {
            "href": "http://openstack.example.com/servers"
                    "/9168b536-cd40-4630-b43f-b259807c6e87",
            "rel": "bookmark"
        }
    ],
    "locked": False,
    "metadata": {
        "My Server Name": "Apache1"
    },
    "name": "new-server-test",
    "os-extended-volumes:volumes_attached": [
        {
            "delete_on_termination": False,
            "id": "volume_id1"
        },
        {
            "delete_on_termination": False,
            "id": "volume_id2"
        }
    ],
    "progress": 0,
    "security_groups": [
        {
            "name": "default"
        }
    ],
    "status": "ACTIVE",
    "tags": [],
    "tenant_id": "6f70656e737461636b20342065766572",
    "updated": "2017-02-14T19:24:00Z",
    "user_id": "fake"
}
SERVER_RESPONSE = {'server': SERVER}
