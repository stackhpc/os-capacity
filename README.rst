os-capacity
===========

This is a prototype tool to extract capacity information.

Install
-------

First lets get the code downloaded:

.. code::

    git clone https://github.com/JohnGarbutt/os-capacity.git
    cd os-capacity

Now lets get that installed inside a virtual environment:

.. code::

    python3 -m virtualenv .venv
    source .venv/bin/activate
    pip install -U .

Prometheus Exporter
-------------------

Assuming you have clouds.yaml in the right place,
and those credentials have read access to the Placement API, Nova API and Keystone APIs,
you can run the exporter doing something like this:

.. code::

   export OS_CLIENT_CONFIG_FILE=myappcred.yaml
   export OS_CLOUD=openstack

   ./os_capacity/prometheus.py &
   curl localhost:9000 > mytestrun
   cat mytestrun

Or just run via docker or similar:::

   docker run -d --name os_capacity \
     --mount type=bind,source=/etc/kolla/os-capacity/,target=/etc/openstack \
     --env OS_CLOUD=openstack --env OS_CLIENT_CONFIG_FILE=/etc/openstack/clouds.yaml \
     -p 9000:9000 ghcr.io/stackhpc/os-capacity:e08ecb8
   curl localhost:9000


We aslo have the following optional environment variables:

* OS_CAPACITY_EXPORTER_PORT = 9000
* OS_CAPACITY_EXPORTER_LISTEN_ADDRESS = "0.0.0.0"
* OS_CAPACITY_SKIP_AGGREGATE_LOOKUP = 0
* OS_CAPACITY_SKIP_PROJECT_USAGE = 0
* OS_CAPACITY_SKIP_HOST_USAGE = 0

Here is some example output from the exporter:::

   # HELP openstack_free_capacity_by_flavor_total Free capacity if you fill the cloud full of each flavor
   # TYPE openstack_free_capacity_by_flavor_total gauge
   openstack_free_capacity_by_flavor_total{flavor_name="amphora"} 821.0
   openstack_free_capacity_by_flavor_total{flavor_name="bmtest"} 1.0
   openstack_free_capacity_by_flavor_total{flavor_name="large"} 46.0
   openstack_free_capacity_by_flavor_total{flavor_name="medium"} 94.0
   openstack_free_capacity_by_flavor_total{flavor_name="small"} 191.0
   openstack_free_capacity_by_flavor_total{flavor_name="tiny"} 385.0
   openstack_free_capacity_by_flavor_total{flavor_name="xlarge"} 19.0
   openstack_free_capacity_by_flavor_total{flavor_name="pinnned.full"} 1.0
   openstack_free_capacity_by_flavor_total{flavor_name="pinnned.half"} 2.0
   openstack_free_capacity_by_flavor_total{flavor_name="pinned.large"} 2.0
   openstack_free_capacity_by_flavor_total{flavor_name="pinned.quarter"} 4.0
   openstack_free_capacity_by_flavor_total{flavor_name="pinned.tiny"} 53.0
   ...
   # HELP openstack_free_capacity_hypervisor_by_flavor Free capacity for each hypervisor if you fill remaining space full of each flavor
   # TYPE openstack_free_capacity_hypervisor_by_flavor gauge
   openstack_free_capacity_hypervisor_by_flavor{az_aggregate="regular",flavor_name="amphora",hypervisor="ctrl1",project_aggregate="test"} 263.0
   ...
   # HELP openstack_project_filter_aggregate Mapping of project_ids to aggregates in the host free capacity info.
   # TYPE openstack_project_filter_aggregate gauge
   openstack_project_filter_aggregate{aggregate="test",project_id="c6992a4f9f5a45fab23114d032fca40b"} 1.0
   ...
   # HELP openstack_project_usage Current placement allocations per project.
   # TYPE openstack_project_usage gauge
   openstack_project_usage{placement_resource="VCPU",project_id="c6992a4f9f5a45fab23114d032fca40b",project_name="test"} 136.0
   openstack_project_usage{placement_resource="MEMORY_MB",project_id="c6992a4f9f5a45fab23114d032fca40b",project_name="test"} 278528.0
   openstack_project_usage{placement_resource="DISK_GB",project_id="c6992a4f9f5a45fab23114d032fca40b",project_name="test"} 1440.0
   ...
   # HELP openstack_project_quota Current quota set to limit max resource allocations per project.
   # TYPE openstack_project_quota gauge
   openstack_project_quota{project_id="c6992a4f9f5a45fab23114d032fca40b",project_name="test",quota_resource="CPUS"} -1.0
   openstack_project_quota{project_id="c6992a4f9f5a45fab23114d032fca40b",project_name="test",quota_resource="MEMORY_MB"} -1.0
   ...
   # HELP openstack_hypervisor_placement_allocated Currently allocated resource for each provider in placement.
   # TYPE openstack_hypervisor_placement_allocated gauge
   openstack_hypervisor_placement_allocated{hypervisor="ctrl1",resource="VCPU"} 65.0
   openstack_hypervisor_placement_allocated{hypervisor="ctrl1",resource="MEMORY_MB"} 132096.0
   openstack_hypervisor_placement_allocated{hypervisor="ctrl1",resource="DISK_GB"} 485.0
   ...
   # HELP openstack_hypervisor_placement_allocatable_capacity The total allocatable resource in the placement inventory.
   # TYPE openstack_hypervisor_placement_allocatable_capacity gauge
   openstack_hypervisor_placement_allocatable_capacity{hypervisor="ctrl1",resource="VCPU"} 320.0
   openstack_hypervisor_placement_allocatable_capacity{hypervisor="ctrl1",resource="MEMORY_MB"} 622635.0
   openstack_hypervisor_placement_allocatable_capacity{hypervisor="ctrl1",resource="DISK_GB"} 19551.0

Example of a prometheus scrape config:::

   - job_name: os_capacity
     relabel_configs:
    - regex: ([^:]+):\d+
      source_labels:
      - __address__
      target_label: instance
    static_configs:
    - targets:
      - localhost:9000
    scrape_interval: 2m
    scrape_timeout: 1m

Once that is in prometheus, and its not timing out, you can visualise the data
by importing this grafana dashboard:
https://raw.githubusercontent.com/stackhpc/os-capacity/master/example_grafana_dashboard.json
