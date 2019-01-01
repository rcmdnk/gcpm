#!/usr/bin/env bash

exec_cmd () {
  echo "$ $*"
  eval "$*"
}
{
  exec_cmd cd /root
  exec_cmd curl -LOkSs   https://github.com/mickaneda/gcpm-puppet/archive/master.tar.gz
  exec_cmd tar xzf master.tar.gz
  exec_cmd cd gcpm-puppet-master
  exec_cmd ./setup.sh
  exec_cmd /opt/puppetlabs/bin/puppet apply /etc/puppetlabs/code/environments/production/manifests/site.pp --verbose >& /root/puppet.log
  exec_cmd cd /root
  exec_cmd rm -rf master.tar.gz gcpm-puppet-master
  cat /root/puppet.log
  if grep -q "Error" /root/puppet.log || ! grep -q "Applied catalog" /root/puppet.log;then
    exec_cmd touch startup_failed
    exit 1
  fi
  exec_cmd touch startup_finished
} >& /root/startup.log
