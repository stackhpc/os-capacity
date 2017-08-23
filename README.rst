os-capacity
===========

This is a prototype tool to extract pototype information.

.. note::

    This is currently quite specific to Ironic powered OpenStack Nova clouds.

Install
-------

First lets get the code downloaded:

.. code::

    git clone https://github.com/JohnGarbutt/os-capacity.git
    cd os-capacity

Now lets get that installed inside a virtual enviroment:

.. code::

    virtualenv .venv-test
    source .venv-test/bin/activate
    pip install -U .

Configuration
-------------

The easiest way to configure this is to populate a typical OpenStack RC file:

.. code::

    cat > openrc <<EOF
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

    source openrc

Usage
-----

When opening a new terminal, first activate the venv and the configuration:

.. code::

    source .venv-test/bin/activate
    source openrc


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

You can look at all the different types of servers and capacity used:

.. code::

    (.venv-test) $ os-capacity resources group
    +----------------------------------+-------+------+------+-------------+
    | Resource Class Groups            | Total | Used | Free | Flavors     |
    +----------------------------------+-------+------+------+-------------+
    | VCPU:1,MEMORY_MB:512,DISK_GB:20  |     5 |    1 |    4 | my-flavor-1 |
    | VCPU:2,MEMORY_MB:1024,DISK_GB:40 |     2 |    0 |    2 | my-flavor-2 |
    +----------------------------------+-------+------+------+-------------+

See the online help for more details:

.. code::

    os-capacity help
