# Google Cloud Platform Condor Pool Manager (GCPM)

[![Build Status](https://travis-ci.org/mickaneda/gcpm.svg?branch=master)](https://travis-ci.org/mickaneda/gcpm) ([Coverage report](https://mickaneda.github.io/gcpm/))

HTCondor pool manager for Google Cloud Platform.

## Installation

### Package installation

GCPM can be installed by `pip`:

    $ pip install gcpm

### Service file installation

To install as service, do:

    $ gcpm install

:warning: Service installation is valid only for the system managed by **Systemd**.

If **logrotate** is installed, logrotation definition for **/var/log/gcpm.log** is also installed.

## Configuration file

### Configuration file path

The default configuration file is **~/.config/gcpm/gcpm.yml**.

For service, the configuration file is **/etc/gcpm.yml**.

To change the configuration file, use `--config` option:

    $ gcpm run --config /path/to/my/gcpm.yml

### Configuration file content

A configuration file is YAML format.

Name|Description|Default Value|Mandatory|
:---|:----------|:------------|:--------|
config_dir   | Directory for some gcpm related files.|**~/.config/gcpm/** (user)<br>**/var/cache/gcpm** (service)|No
oatuh_file   | Path to OAuth information file for GCE/GCS usage.|**<config_dir>/oauth**|No
service_account_file | Service account JSON file for GCE/GCS usage.<br>If not specified, OAuth connection is tried.|-|No
project      | Google Cloud Platform Project Name.|-|Yes
zone         | Zone for Google Compute Engine.|-|Yes
machines     | Array of machine settings.<br>Each setting is array of [core, mem, disk, idle, image] (see below).|[]|Yes
machines:core | Number of core of the machine type.|-|Yes
machines:mem | Memory (MB) of the machine type.|-|Yes
machines:disk | Disk size (GB) of the machine type.|-|Yes
machines:max | Limit of the number of instances for the machine type.|-|Yes
machines:idle | Number of idle machines for the machine type.|-|Yes
machines:image | Image of the machine type.|-|Yes
max_cores    | Limit of the total number of cores of all instances.<br>If it is set 0, no limit is applied.|0|No
static       | Array of instance names which should run always.|[]|No
prefix       | Prefix of machine names.|**gcp-wn**|No
preemptible  | 1 for preemptible machines, 0 for not.|0|No
off_timer    | Second to send condor_off after starting.|0|No
network_tag  | Array of GCP network tag.|[]|No
reuse        | 1 to reused terminated instance. Otherwise delete and re-created instances.|0|No
interval     | Second of interval for each loop.|10|No
head_info    | If **head** is empty, head node information is automatically taken for each option:<br>hostname: Hostname<br>ip: IP address<br>gcp: Hostname|**gcp**|No
head         | Head node Hostname/IP address.|""|No
port         | HTCondor port.|9618|No
domain       | Domain of the head node.<br>Set empty to take it from hostnaem.|""|No
admin        | HTCondor admin email address.|""|Yes
owner        | HTCondor owner name.|""|Yes
wait_cmd     | 1 to wait GCE commands result (create/start/stop/delete...).|0|No
bucket       | Bucket name for pool_password file.|""|Yes
storageClass | Storage class name of the bucket.|"REGIONAL"|No
location     | Storage location for the bucket.<br>If empty, it is decided from the **zone**.|""|No
log_file     | Log file path. Empty to put it in stdout.|""|No
log_level    | Log level. (**debug**, **info**, **warning**, **error**, **critical**)|**info**|No
