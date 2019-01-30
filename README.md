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
machines:core     | Number of core of the machine type.|-|Yes
machines:mem      | Memory (MB) of the machine type.|-|Yes
machines:swap     | Swap memory (MB) of the machine type.|Same as mem|No
machines:disk     | Disk size (GB) of the machine type.|-|Yes
machines:max      | Limit of the number of instances for the machine type.|-|Yes
machines:idle     | Number of idle machines for the machine type.|-|Yes
machines:image    | Image of the machine type.|-|Yes
machines:&lt;others&gt; | Other any options can be defined for creating instance.|-|No
max_cores    | Limit of the total number of cores of all instances.<br>If it is set 0, no limit is applied.|0|No
static_wns   | Array of instance names of static worker nodes, which are added as condor worker nodes.|[]|No
required_machines          | Array of machines which should be running other than worker nodes.|[]|No
required_machines:name     | Number of core of the machine type.|-|Yes
required_machines:mem      | Memory (MB) of the machine type.|-|Yes
required_machines:swap     | Swap memory (MB) of the machine type.|Same as mem|No
required_machines:disk     | Disk size (GB) of the machine type.|-|Yes
required_machines:image    | Image of the machine type.|-|Yes
required_machines:&lt;others&gt; | Other any options can be defined for creating instance.|-|No
primary_accounts |User accounts which jobs must run normal worker nodes. See below about primary accounts.|[]|No
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


Note:

* Primary accounts

If primary accounts are set, jobs of **non-primary** accounts can run on test worker nodes.

If there are already max number of 1 core worker nodes
and idle jobs of non-primary accounts are there,
test worker node named **&lt;prefix&gt;-test-1core-XXXX** will be launched
and only non-primary account jobs can run on it.

This able to run such a test job w/o waiting for finishing any normal jobs.

Such test worker nodes can be launched until total cores are smaller than `max_core`.

To use this function effectively, set total of `max` of each core to less than `max_core`.

e.g.)

```yml
---
machines:
  core: 1
  max: 10
machines:
  core: 8
  max:  2
max_core: 20
primary_accounts:
  - condor_primary
```

In this case, normal jobs can launch 10 1-core machines and 2 8-core machines,
then 16 cores are used.

Even if there are a log of idle **condor_primary**'s jobs,
1 core test jobs by other accounts can run: 4 jobs at most.

## Puppet setup

* [mickaneda/puppet-gcpm](https://github.com/mickaneda/puppet-gcpm)

A puppet module for GCPM.

* [mickaneda/gcpm-puppet](https://github.com/mickaneda/gcpm-puppet)

A puppet example to create head (manager) node and worker node with puppet.

* [mickaneda/frontiersquid-puppet](https://github.com/mickaneda/frontiersquid-puppet)

A puppet example to create frontier squid proxy server in GCP.
