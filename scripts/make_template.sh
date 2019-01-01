#!/usr/bin/env bash

name=gcp-wn-template-01
zone=
image_project=centos-cloud
image_family=centos-7
image=""
machine_type=n1-standard-1
boot_disk_size=""

options=(zone image_project image_family image machine_type boot_disk_size)

# Check args
HELP="Usage: $(basename "$0") [-n <name>] [-z <zone>] [-p <image-project>] [-f <image-family>] [-i <image>] [-m <machine-type>] [-h]

Arguments:
-n <name>           Set template machine name (default: $name)
-z <zone>           Set zone (default: $zone)
-p <image-project>  Set image-project (default: $image_project)
-f <image-family>   Set image-family (default: $image_family)
-i <image>          Set image (default: $image)
-m <machine-type>   Set machine-type (default: $machine_type)
-d <boot-disk-size> Set boot-disk-size (default: $boot_disk_size)
-h                  Show help
"
while getopts n:z:p:f:i:m:d:h OPT;do
  case $OPT in
    "n" ) name=$OPTARG ;;
    "z" ) zone=$OPTARG ;;
    "p" ) image_project=$OPTARG ;;
    "f" ) image_family=$OPTARG ;;
    "i" ) image=$OPTARG ;;
    "m" ) machine_type=$OPTARG ;;
    "d" ) boot_disk_size=$OPTARG ;;
    "h" ) echo "$HELP";exit 2;;
    * ) echo "Unknown argument: $OPT";exit 1;;
  esac
done
shift $((OPTIND - 1))

if [[ "$name" != gcp-wn* ]];then
  echo "Worker node template name must be 'gcp-wn*'"
  exit 1
fi

$(dirname $0)/check_gcloud.sh
ret=$?
[[ $ret -ne 0 ]] && exit $ret

option=""
for o in "${options[@]}";do
  eval "[ -n \"\$$o\" ]" && eval "option=\"$option --${o//_/-}=\$$o"\"
done
cmd="gcloud compute instances create $name $option --metadata-from-file startup-script=./startup_worker.sh"
echo "\$ $cmd"
$cmd
ret=$?
if [ $ret -ne 0 ];then
  echo "Failed to make template, please check."
  exit 1
fi

echo "Waiting for setting up template..."
try=0
while :;do
  root_files=$(gcloud compute ssh "$name" --command "sudo ls /root" 2>/dev/null)
  if echo "$root_files"|grep -q startup_finished;then
    echo "Template: $name was created"
    break
  fi
  if echo "$root_files"|grep -q startup_failed;then
    echo "Failed during setup template: $name, please check."
    exit 1
  fi
  if [ $try -gt 100 ];then
    echo "Template: $name has not been set up, please check."
    exit 1
  fi
  sleep 5
done

