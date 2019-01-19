# -*- coding: utf-8 -*-

"""
    Module to provide utilities
"""


def expand(path):
    import os
    return os.path.expandvars(os.path.expanduser(path))


def proc(cmd):
    import sys
    import shlex
    import subprocess
    if type(cmd) != list:
        cmd = shlex.split(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if sys.version_info.major > 2:
        stdout = stdout.decode()
        stderr = stderr.decode()
    return (p.returncode, stdout, stderr)


def make_startup_script(core, mem, disk, image, preemptible, admin,
                        head, port, domain, owner, bucket, off_timer=0,
                        slot_number=1):
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

sed -i"" 's/FIXME_SLOT_NUMBER/{slot_number}/' \
/etc/condor/config.d/20_workernode.config

gsutil cp "gs://{bucket}/pool_password" /etc/condor/
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
                                       bucket=bucket, slot_number=slot_number)

    if off_timer != 0:
        content += """
sleep {off_timer}
condor_off -peaceful -startd
date >> /root/condor_off""".format(off_timer=off_timer)
    return content


def make_shutdown_script():
    content = """#!/usr/bin/env bash
preempted=$(\
curl "http://metadata.google.internal/computeMetadata/v1/instance/preempted" \
-H "Metadata-Flavor: Google")
echo "{{\\"date\\": \\"$(date +%s)\\", \\"preempted\\": ${{preempted}}}}" \
>>/var/log/shutdown.log""".format()
    return content
