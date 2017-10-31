#
# Example script to use with cron to regular send metrics to Monasca
#

# Example crontab entry to run this script every 5 mins:
#
# */5 * * * * /home/stack/os-capacity/cron/example.sh > /tmp/metrics_last.log

set -e

source /home/stack/os-capacity/.openrc
source /home/stack/os-capacity/.venv-test/bin/activate

export OS_CAPACITY_SEND_METRICS=1

os-capacity usages group
os-capacity resources group
