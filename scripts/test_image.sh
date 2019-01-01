#!/usr/bin/env bash
name=gcp-test-wn-01
zone=
image=gcp-wn-image-01
machine_type=n1-standard-1

options=(zone image machine_type)

# Check args
HELP="Usage: $(basename "$0") [-n <name>] [-z <zone>] [-i <image>] [-m <machine-type>] [-h]

Arguments:
-n <name>           Set template machine name (default: $name)
-z <zone>           Set zone (default: $zone)
-i <image>          Set image (default: $image)
-m <machine-type>   Set machine-type (default: $machine_type)
-h                  Show help
"
while getopts n:z:i:m:h OPT;do
  case $OPT in
    "n" ) name=$OPTARG ;;
    "z" ) zone=$OPTARG ;;
    "i" ) image=$OPTARG ;;
    "m" ) machine_type=$OPTARG ;;
    "h" ) echo "$HELP";exit 2;;
    * ) echo "Unknown argument: $OPT";exit 1;;
  esac
done
shift $((OPTIND - 1))

./check_gcloud.sh
ret=$?
[[ $ret -ne 0 ]] && exit $ret

option=""
for o in "${options[@]}";do
  eval "[ -n \"\$$o\" ]" && eval "option=\"$option --${o//_/-}=\$$o"\"
done
cmd="gcloud compute instances create $name $option"
echo "\$ $cmd"
$cmd
ret=$?
if [ $ret -ne 0 ];then
  echo "Failed to make template, please check."
  exit 1
fi

try=0
while :;do
  root_files=$(gcloud compute ssh "$name" --command "sudo ls /root" 2>/dev/null)
  if echo "$root_files"|grep -q startup_finished;then
    echo "WN image: $image OK"
    break
  fi
  if echo "$root_files"|grep -q startup_failed;then
    echo "WN image: $name seems failed during setup, please check"
    exit 1
  fi
  if [ $try -gt 100 ];then
    echo "WN image: $name seems broken, please check"
    exit 1
  fi
  sleep 5
done

echo y|gcloud compute instances delete $name
