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
import openstack
from prometheus_client import core as prom_core

RETRY_COUNT = 3


class OpenStackAPITestCollector(object):
    def __init__(self):
        openstack.connect()
        print("got openstack connection\n")

    def _check_compute(self, conn):
        for i in range(RETRY_COUNT):
            flavors = list(conn.compute.flavors())
        flavor_count = prom_core.GaugeMetricFamily(
            "openstack_flavor_count",
            "The number of flavors in the OpenStack deployment.",
            labels=["project_id"],
        )
        flavor_count.add_metric([conn.current_project_id], len(flavors))

        for i in range(RETRY_COUNT):
            servers = list(conn.compute.servers())
        server_count = prom_core.GaugeMetricFamily(
            "openstack_server_count",
            "The number of servers in the OpenStack deployment.",
            labels=["project_id"],
        )
        server_count.add_metric([conn.current_project_id], len(servers))
        return [flavor_count, server_count]

    def _check_images(self, conn):
        for i in range(RETRY_COUNT):
            images = list(conn.image.images())
        image_count = prom_core.GaugeMetricFamily(
            "openstack_image_count",
            "The number of images in the OpenStack deployment.",
            labels=["project_id"],
        )
        image_count.add_metric([conn.current_project_id], len(images))
        return [image_count]

    def _check_volumes(self, conn):
        for i in range(RETRY_COUNT):
            volumes = list(conn.block_storage.volumes())
        volume_count = prom_core.GaugeMetricFamily(
            "openstack_volume_count",
            "The number of volumes in the OpenStack deployment.",
            labels=["project_id"],
        )
        volume_count.add_metric([conn.current_project_id], len(volumes))
        return [volume_count]

    def _check_ironic(self, conn):
        for i in range(RETRY_COUNT):
            nodes = list(conn.bare_metal.nodes())
        ironic_node_count = prom_core.GaugeMetricFamily(
            "openstack_ironic_node_count",
            "The number of ironic nodes in the OpenStack deployment.",
            labels=["project_id"],
        )
        ironic_node_count.add_metric([conn.current_project_id], len(nodes))
        return [ironic_node_count]

    def _check_identity(self, conn):
        user = conn.current_user_id
        for i in range(RETRY_COUNT):
            projects = list(conn.identity.user_projects(user))
        project_count = prom_core.GaugeMetricFamily(
            "openstack_project_count",
            "The number of projects in the OpenStack deployment.",
            labels=["project_id"],
        )
        project_count.add_metric([conn.current_project_id], len(projects))
        return [project_count]

    def _check_network(self, conn):
        for i in range(RETRY_COUNT):
            networks = list(conn.network.networks())
        network_count = prom_core.GaugeMetricFamily(
            "openstack_network_count",
            "The number of networks in the OpenStack deployment.",
            labels=["project_id"],
        )
        network_count.add_metric([], len(networks))

        for i in range(RETRY_COUNT):
            ports = list(conn.network.ports())
        port_count = prom_core.GaugeMetricFamily(
            "openstack_port_count",
            "The number of ports in the OpenStack deployment.",
            labels=["project_id"],
        )
        port_count.add_metric([conn.current_project_id], len(ports))
        return [network_count, port_count]

    def _check_load_balancer(self, conn):
        for i in range(RETRY_COUNT):
            lbs = list(conn.load_balancer.load_balancers())
        lb_count = prom_core.GaugeMetricFamily(
            "openstack_load_balancer_count",
            "The number of load balancers in the OpenStack deployment.",
            labels=["project_id"],
        )
        lb_count.add_metric([conn.current_project_id], len(lbs))
        return [lb_count]

    def collect(self):
        openstack.enable_logging(debug=False)
        conn = openstack.connect()
        print("collecting api test metrics\n")
        guages = []

        guages += self._check_compute(conn)
        guages += self._check_images(conn)
        guages += self._check_volumes(conn)
        guages += self._check_ironic(conn)
        guages += self._check_identity(conn)
        guages += self._check_network(conn)
        guages += self._check_load_balancer(conn)

        print("finished collecting metrics\n")
        return guages
