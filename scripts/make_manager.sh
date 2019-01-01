#!/usr/bin/env bash

name=gcp-ce-01
zone=
image_project=centos-cloud
image_family=centos-7
image=""
machine_type=n1-standard-1
admin="root"
collector_name="My Condor Pool"
bucket=""
gcpm_conf=""
service_account=""

options=(zone image_project image_family image machine_type boot_disk_size)

# Check args
HELP="Usage: $(basename "$0") [-n <name>] [-z <zone>] [-p <image-project>] [-f <image-family>] [-i <image>] [-m <machine-type>] [-a <admin maiil> ] [-c <collector_name>] [-b <bucket>] [-s <service_account>] [-h]

Arguments:
-n <name>            Set template machine name (default: $name)
-z <zone>            Set zone (default: $zone)
-p <image-project>   Set image-project (default: $image_project)
-f <image-family>    Set image-family (default: $image_family)
-i <image>           Set image (default: $image)
-m <machine-type>    Set machine-type (default: $machine_type)
-d <boot-disk-size>  Set boot-disk-size (default: $boot_disk_size)
-a <admin mail>      Set admin's mail address (default: $admin)
-c <collector_name>  Set HTCondor pool's short description (default: $collector_name)
-b <bucket>          Set bucket name for pool_password (default: $bucket)
-g <conf>            Set gcpm config file (default: $gcpm_conf)
-s <service_account> Set service account json file for gcloud (default: $service_account)
-h                   Show help
"

while getopts n:z:p:f:i:m:d:a:c:b:g:s:h OPT;do
  case $OPT in
    "n" ) name=$OPTARG ;;
    "z" ) zone=$OPTARG ;;
    "p" ) image_project=$OPTARG ;;
    "f" ) image_family=$OPTARG ;;
    "i" ) image=$OPTARG ;;
    "m" ) machine_type=$OPTARG ;;
    "d" ) boot_disk_size=$OPTARG ;;
    "a" ) admin=$OPTARG ;;
    "c" ) collector_name=$OPTARG ;;
    "b" ) bucket=$OPTARG ;;
    "g" ) gcpm_conf=$OPTARG ;;
    "s" ) service_account=$OPTARG ;;
    "h" ) echo "$HELP";exit 2;;
    * ) echo "Unknown argument: $OPT";exit 1;;
  esac
done
shift $((OPTIND - 1))

if [[ "$name" != gcp-ce* ]];then
  echo "Manager name must be 'gcp-ce*'"
  exit 1
fi

$(dirname $0)/check_gcloud.sh
ret=$?
[[ $ret -ne 0 ]] && exit $ret

# Make startup script
startup=$(mktemp)
cat << EOF > "$startup"
#!/usr/bin/env bash

exec_cmd () {
  echo "$ \$*"
  eval "\$*"
}
{
  exec_cmd cd /root
  exec_cmd curl -LOkSs   https://github.com/mickaneda/gcpm-puppet/archive/master.tar.gz
  exec_cmd tar xzf master.tar.gz
  exec_cmd cd gcpm-puppet-master
  exec_cmd ./setup.sh
  exec_cmd "/opt/puppetlabs/bin/puppet apply /etc/puppetlabs/code/environments/production/manifests/site.pp --verbose >& /root/puppet.log"
  exec_cmd cd /root
  exec_cmd rm -rf master.tar.gz gcpm-puppet-master
  cat /root/puppet.log
  if grep -q "Error" /root/puppet.log || ! grep -q "Applied catalog" /root/puppet.log;then
    exec_cmd cd /root
    exec_cmd touch startup_failed
    exit 1
  fi

  exec_cmd "sed -i\"\" 's/FIXME_ADMIN/${admin}/' /etc/condor/config.d/00_config_local.config"

  exec_cmd "sed -i\"\" 's/FIXME_HOST/\${HOSTNAME}/' /etc/condor/config.d/10_security.config"
  exec_cmd "sed -i\"\" 's/FIXME_DOMAIN/\$(hostname -d)/' /etc/condor/config.d/10_security.config"
  exec_cmd "sed -i\"\" 's/FIXME_PRIVATE_DOMAIN/\$(hostname -d)/' /etc/condor/config.d/10_security.config"

  exec_cmd "sed -i\"\" 's/FIXME_COLLECTOR_NAME/${collector_name}/' /etc/condor/config.d/22_manager.config"

  if [ -n "$service_account" ];then
    echo "$(if [ -n "$service_account" ];then cat "$service_account"|sed 's/"/\\"/g';fi)" >/root/service_account.json
    gcloud auth activate-service-account --key-file /root/service_account.json
    ret=\$?
    if [ \$ret -ne 0 ];then
      echo "Failed at gcloud auth"
      exec_cmd cd /root
      exec_cmd touch startup_failed
      exit 1
    fi
  fi

  if [ -n "${bucket}" ];then
    if ! gsutil ls|grep -q $bucket;then
      exec_cmd gsutil mb ${bucket}
    fi
    if ! gsutil ls|grep -q $bucket/pool_password;then
      condor_store_cred add -c -f ./pool_password  -p \$(openssl rand -base64 12|fold -w 10|head -1)
      exec_cmd gsutil cp pool_password ${bucket}/
      rm -f pool_password
    fi
    exec_cmd gsutil cp ${bucket}/pool_password /etc/condor/
    exec_cmd chmod 600 /etc/condor/pool_password
    exec_cmd systemctl enable condor
    exec_cmd systemctl start condor
    if ! systemctl status condor|grep -q running;then
      echo "Failed to start condor"
      exec_cmd cd /root
      exec_cmd touch startup_failed
      exit 1
    fi
  fi

  exec_cmd cd /root
  exec_cmd git clone https://github.com/mickaneda/gcp_condor_pool_manager
  exec_cmd cd ./gcp_condor_pool_manager
  exec_cmd ./scripts/install.sh

  if [ -n "$gcpm_conf" ];then
    echo "$(if [ -n "$gcpm_conf" ];then cat "$gcpm_conf"|sed 's/"/\\"/g';fi)" >/etc/gcpm.conf
    echo "/etc/gcpm.conf was updated"
    if [ -n "${bucket}" ] && [ -n "$service_account" ];then
      exec_cmd systemctl enable gcpm
      exec_cmd systemctl start gcpm
      if ! systemctl status gcpm|grep -q running;then
        echo "Failed to start gcpm"
        exec_cmd cd /root
        exec_cmd touch startup_failed
        exit 1
      fi
    fi
  fi

  exec_cmd cd /root
  exec_cmd touch startup_finished
} >& /root/startup.log
EOF

option=""
for o in "${options[@]}";do
  eval "[ -n \"\$$o\" ]" && eval "option=\"$option --${o//_/-}=\$$o"\"
done

cmd="gcloud compute instances create $name $option --metadata-from-file startup-script=$startup"
echo "\$ $cmd"
$cmd
ret=$?
if [ $ret -ne 0 ];then
  echo "Failed to make template, please check."
  exit 1
fi

echo "Waiting for setting up manager..."
try=0
while :;do
  root_files=$(gcloud compute ssh "$name" --command "sudo ls /root" 2>/dev/null)
  if echo "$root_files"|grep -q startup_finished;then
    echo "Manager: $name was created"
    break
  fi
  if echo "$root_files"|grep -q startup_failed;then
    echo "Failed during setup manager: $name, please check."
    exit 1
  fi
  if [ $try -gt 100 ];then
    echo "Manager: $name has not been set up, please check."
    exit 1
  fi
  sleep 5
done

if [ -z "${bucket}" ];then
  echo "You didn't set bucket (-b <bucket>), therefore dummy pool_password will be installed."
  echo "Please replace it and start condor ('systemctl enable condor && systemctl start condor') after the manager is set up."
fi
if [ -z "${gcpm_conf}" ];then
  echo "You didn't set gcpm configuration file (-g <gcpm_conf>), therefore gcpm has not been started."
  echo "Please update /etc/gcpm.conf and start gcpm ('systemctl enable gcpm && systemctl start gcpm')."
fi
if [ -z "${service_account}" ];then
  echo "You didn't set service account file for gcloud  (-s <service_account>), therefore gcpm has not been started."
  echo "Please setup account in the manager, and start gcpm ('systemctl enable gcpm && systemctl start gcpm')."
fi
