# -*- coding: utf-8 -*-

"""
    Module to mange Google Cloud Storage.
"""


import os
from .utils import expand


__SERVICE_FILE__ = "/usr/lib/systemd/system/gcpm.service"
__LOGROTATE_FILE__ = "/etc/logrotate.d/gcpm.conf"


def make_file(filename, content="", mkdir=True):
    filename = expand(filename)
    directory = os.path.dirname(filename)
    if not os.path.isdir(directory):
        if mkdir:
            os.makedirs(directory)
        else:
            return False
    with open(filename, mode='w') as f:
            f.write(content)
    return True


def rm_file(filename):
    if not os.path.isfile(filename):
        return
    os.remove(filename)


def make_startup_script(filename, core, mem, disk, image, preemptible, admin,
                        head, port, domain, owner, bucket, off_timer=0,
                        mkdir=True):
    content = """#!/usr/bin/env bash
echo "{{\\"date\\": \\"$(date +%s)\\", \\"core\\": {core},\\"mem\\": {mem}, \
\\"disk\\": {disk}, \\"image\\": \\"{image}\\", \
\\"preemptible\\": {preemptible}}}" >/var/log/nodeinfo.log

sed -i"" 's/FIXME_ADMIN/{admin}/' /etc/condor/config.d/00_config_local.config

sed -i"" 's/FIXME_HOST/{head}/' /etc/condor/config.d/10_security.config
sed -i"" 's/FIXME_PORT/{port}/' /etc/condor/config.d/10_security.config
sed -i"" 's/FIXME_DOMAIN/{domain}/' /etc/condor/config.d/10_security.config
sed -i"" "s/FIXME_PRIVATE_DOMAIN/$(hostname -d)/" \
/etc/condor/config.d/10_security.config

sed -i"" 's/FIXME_OWNER/{owner}/' /etc/condor/config.d/20_workernode.config
sed -i"" 's/FIXME_CORE/{core}/' /etc/condor/config.d/20_workernode.config
sed -i"" 's/FIXME_MEM/{mem}/' /etc/condor/config.d/20_workernode.config

gsutil cp "${bucket}/pool_password" /etc/condor/
chmod 600 /etc/condor/pool_password
systemctl enable condor
systemctl start condor
while :;do
  condor_reconfig
  status="$(condor_status | grep "${{HOSTNAME}}")"
  if [ -n "$status" ];then
    break
  fi
  sleep 10
done
date >> /root/condor_started""".format(core=core, mem=mem, disk=disk,
                                       image=image, preemptible=preemptible,
                                       admin=admin, head=head, port=port,
                                       domain=domain, owner=owner,
                                       bucket=bucket)

    if off_timer != 0:
        content += """
sleep {off_timer}
condor_off -peaceful -startd
date >> /root/condor_off""".format(off_timer=off_timer)
    make_file(filename, content, mkdir)


def make_shutdown_script(filename, mkdir=True):
    content = """#!/usr/bin/env bash
preempted=$(\
curl "http://metadata.google.internal/computeMetadata/v1/instance/preempted" \
-H "Metadata-Flavor: Google")
echo "{{\\"date\\": \\"$(date +%s)\\", \\"preempted\\": ${{preempted}}}}" \
>>/var/log/shutdown.log""".format()
    make_file(filename, content, mkdir)


def make_service(filename=__SERVICE_FILE__, mkdir=True):
    content = """[Unit]
Description = HTCondor pool manager for Google Cloud Platform

[Service]
Environment = "PATH={path}"
ExecStart = /usr/bin/gcpm service
ExecStop = /usr/bin/kill -p $MAINPID
Restart = always
StandardOutput = syslog
StandardError = syslog
SyslogIdentifier = gcpm

[Install]
WantedBy = multi-user.target""".format(path=os.environ["PATH"])
    make_file(filename, content, mkdir)


def rm_service(filename=__SERVICE_FILE__):
    rm_file(filename)


def make_logrotate(filename=__LOGROTATE_FILE__, mkdir=True):
    content = """/var/log/gcpm.log {{
  missingok
  rotate 10
  dateext
  delaycompress
  daily
  minsize 100M
  postrotate
      systemctl restart gcpm
  endscript
}}""".format()
    make_file(filename, content, mkdir)


def rm_logrotate(filename=__LOGROTATE_FILE__):
    rm_file(filename)
