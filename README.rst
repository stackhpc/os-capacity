os-capacity
===========

This is a prototype tool to extract capacity information.

.. note::

    This is currently quite specific to Ironic powered OpenStack Nova clouds.

Install
-------

First lets get the code downloaded:

.. code::

    git clone https://github.com/JohnGarbutt/os-capacity.git
    cd os-capacity

Now lets get that installed inside a virtual environment:

.. code::

    virtualenv .venv-test
    source .venv-test/bin/activate
    pip install -U .

Prometheus Exporter
-------------------

Assuming you have clouds.yaml in the right place and OS_CLOUD set:

.. code::

   ./os_capacity/prometheus.py
   openstack_total_capacity_per_flavor{flavor="small"} 1
   openstack_capacity_by_hostname{hypervisor="aio",flavor="small"} 1


TODOs we need support for:

* add request filter support for require_tenant_aggregate,
  map_az_to_placement_aggregate and compute_status_filter

Configuration
-------------

The easiest way to configure this is to populate a typical OpenStack RC file:

.. code::

    cat > .openrc <<EOF
    export OS_AUTH_URL=http://keystone.example.com:5000/v3
    export OS_PROJECT_ID=
    export OS_PROJECT_NAME=
    export OS_USER_DOMAIN_NAME=
    export OS_PROJECT_DOMAIN_NAME=
    export OS_USERNAME=
    export OS_REGION_NAME=
    export OS_INTERFACE=
    export OS_IDENTITY_API_VERSION=3
    export OS_AUTH_PLUGIN=v3password
    echo "Please enter your OpenStack Password for project $OS_PROJECT_NAME as user $OS_USERNAME: "
    read -sr OS_PASSWORD_INPUT
    export OS_PASSWORD=$OS_PASSWORD_INPUT
    EOF

    source .openrc

Some openrc files don't contain the OS_AUTH_PLUGIN and OS_PROJECT_DOMAIN_NAME
variables, but os-capacity requires that those are set.

Usage
-----

When opening a new terminal, first activate the venv and the configuration:

.. code::

    source .venv-test/bin/activate
    source .openrc


You can do things like list all flavors:

.. code::

    (.venv-test) $ os-capacity flavor list
    +--------------------------------------+-------------+-------+--------+---------+
    | UUID                                 | Name        | VCPUs | RAM MB | DISK GB |
    +--------------------------------------+-------------+-------+--------+---------+
    | 2622d978-7072-484d-8c7a-144a308c2709 | my-flavor-1 |     1 |    512 |      20 |
    | 45de641c-950e-434b-9c2e-6f76b120f85c | my-flavor-2 |     2 |   1024 |      40 |
    +--------------------------------------+-------------+-------+--------+---------+

If you want to see all the REST API calls made, use the verbose flag, and you
can also get the output in json format by adding the format flag:

.. code::

    (.venv-test) $ os-capacity -v flavor list -f json

You can look at all the different types of resources and amount used:

.. code::

    (.venv-test) $ os-capacity resources group
    +----------------------------------+-------+------+------+-------------+
    | Resource Class Groups            | Total | Used | Free | Flavors     |
    +----------------------------------+-------+------+------+-------------+
    | VCPU:1,MEMORY_MB:512,DISK_GB:20  |     5 |    1 |    4 | my-flavor-1 |
    | VCPU:2,MEMORY_MB:1024,DISK_GB:40 |     2 |    0 |    2 | my-flavor-2 |
    +----------------------------------+-------+------+------+-------------+


You can also look at the usage grouped by project or user or total usage:

.. code::

    (.venv-test) $ os-capacity usages group user --max-width 70
    +----------------------+----------------------+----------------------+
    | User                 | Current Usage        | Usage Days           |
    +----------------------+----------------------+----------------------+
    | 1e6abb726dd04d4eb4b8 | Count:4,             | Count:410,           |
    | 94e19c397d5e         | DISK_GB:1484,        | DISK_GB:152110,      |
    |                      | MEMORY_MB:524288,    | MEMORY_MB:53739520,  |
    |                      | VCPU:256             | VCPU:26240           |
    | 4661c3e5f2804696ba26 | Count:1,             | Count:3,             |
    | 56b50dbd0f3d         | DISK_GB:371,         | DISK_GB:1113,        |
    |                      | MEMORY_MB:131072,    | MEMORY_MB:393216,    |
    |                      | VCPU:64              | VCPU:192             |
    +----------------------+----------------------+----------------------+

See the online help for more details:

.. code::

    os-capacity help
    usage: os-capacity [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

    OS-Capacity (StackHPC) Command Line Interface (CLI)

    optional arguments:
      --version            show program's version number and exit
      -v, --verbose        Increase verbosity of output. Can be repeated.
      -q, --quiet          Suppress output except warnings and errors.
      --log-file LOG_FILE  Specify a file to log output. Disabled by default.
      -h, --help           Show help message and exit.
      --debug              Show tracebacks on errors.

    Commands:
      complete       print bash completion command
      flavor list    List all the flavors.
      help           print detailed help for another command
      prometheus  To be run as node exporter textfile collector
      resources all  List all resource providers, with their resources and servers.
      resources group  Lists counts of resource providers with similar inventories.
      usages all     List all current resource usages.
      usages group   Group usage by specified key (by user or project).
