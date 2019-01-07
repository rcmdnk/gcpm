#!/usr/bin/env bash
echo "{\"date\": \"$(date +%s)\", \"core\": 8,\"mem\": 2560, \"disk\": 150, \"image\": \"test-image\", \"preemptible\": 1}" >/var/log/nodeinfo.log

sed -i"" 's/FIXME_ADMIN/admin/' /etc/condor/config.d/00_config_local.config

sed -i"" 's/FIXME_HOST/head-node/' /etc/condor/config.d/10_security.config
sed -i"" 's/FIXME_PORT/1234/' /etc/condor/config.d/10_security.config
sed -i"" 's/FIXME_DOMAIN/example.com/' /etc/condor/config.d/10_security.config
sed -i"" "s/FIXME_PRIVATE_DOMAIN/$(hostname -d)/" /etc/condor/config.d/10_security.config

sed -i"" 's/FIXME_OWNER/owner/' /etc/condor/config.d/20_workernode.config
sed -i"" 's/FIXME_CORE/8/' /etc/condor/config.d/20_workernode.config
sed -i"" 's/FIXME_MEM/2560/' /etc/condor/config.d/20_workernode.config

gsutil cp "$test-bucket/pool_password" /etc/condor/
chmod 600 /etc/condor/pool_password
systemctl enable condor
systemctl start condor
while :;do
  condor_reconfig
  status="$(condor_status | grep "${HOSTNAME}")"
  if [ -n "$status" ];then
    break
  fi
  sleep 10
done
date >> /root/condor_started
sleep 600
condor_off -peaceful -startd
date >> /root/condor_off