# gcp_condor_pool_manager (gcpm)

HTCondor pool manager for Google Cloud Platform.

## Installation

### User install
Install **bin/gcpm** in any directory in PATH.

Prepare **~/.config/gcp_condor_pool_manager/config**.

An example file of configuration file is **./etc/gcpm.conf**.

### System install

gcpm can be run as daemon service of Systemd.

To install it, do:

    $ curl -fsSL https://raw.github.com/mikaneda/gcp_condor_pool_manager/install/install.sh| sh

Or get gcp_condor_pool_manager repository and run:

    # ./scripts/install.sh.

Template configuration file is installed as **/etc/gcpm.conf**.

Edit configuration file, and then

    # systemctl enable gcpm
    # systemctl start gcpm

### Configuration file

See an example of configuration file: **./etc/gcpm.conf**.

For max, core, mem, disk, and image, multiple settings can be set separated by ",".

## Usage

### Set pool_password

At head node, install HTCondor and create pool_password file:

    $ cd /etc/condor
    $ condor_store_cred -f ./pool_password

Then, send it to Google Cloud Storage:

   $ gcpm -p /etc/condor/pool_password

Set `bucket` in your config file. (It must be used even by others. Set unique name.)

### Manage pool

Run gcpm:

    $ gcpm

If you want to load different config file, use `-f`:

   $ gcpm -f /path/to/my_config

### Edit configuration file

    $ gcpm -e

## Image preparation

Example puppet settings can be found in [gcpm-puppet](https://github.com/mickaneda/gcpm-puppet)

By using gcpm-puppet, you can easily make image by:

    $ ./scripts/make_image.sh

This will make image **gcp-wn-image-01** (based on CentOS 7).

You can check the image by

    $ ./scripts/test_image.sh

If you want to modify the image,
it is useful to make template by gcpm-puppet.

    $ ./scripts/make_template.sh

This will make instance **gcp-wn-template-01**.
Then you can login the instance and modify settings.

An image can be easily made by using
[gcp-tools](https://github.com/mickaneda/gcp-tools):

    $ git clone https://github.com/mickaneda/gcp-tools
    $ export PATH=$PATH:./gcp-tools/bin
    $ gce make_image gcp-wn-template-01 gcp-wn-image-01

## Make Manager

A manager host also can be setup by [gcpm-puppet](https://github.com/mickaneda/gcpm-puppet).

You can easily make a manager by:

    $ ./scripts/make_manager.sh -b gs://<bucket-name> -g <path/to/gcpm.conf> -s <path/to/gcp/auth/file.json>

HOSTNAME is **gcp-ce-01** by default.

Before run it, prepare **gcpm.conf**.
You can start from the example: **./etc/gcpm.conf**.

Please set same bucket-name in **gcpm.conf** and an argument for `-b`.

You need authentication file for GCP which has right to manage Google Compute Engine and Storage.

There is a test user **condor_test** and some test files are in its home.
To test, do:

    $ gcloud compute ssh gce-ce-01
    # @gce-ce-01
    $ sudo su
    # su condor_test
    $ cd
    $ ls
    test.sh       test.sub      test8.sh      test8.sub
    $ condor_submit test.sub
    $ condor_submit test.sub
    $ condor_submit test.sub
    $ condor_submit test.sub
    $ condor_submit test8.sub
    $ condor_submit test8.sub
    $ condor_submit test8.sub
    $ condor_submit test8.sub
    $ condor_status
    $ condor_q
    $ # etc...

`test.sub` and `test8.sub` are single cpu job and 8 cpus job, respectively.

The default **gcpm.conf** has 1 cpu and 8 cpus settings,
then `gcpm` will create instances of them.

After some time (a few sec~1 min), `condor_status` will show new instance and jobs will start.

