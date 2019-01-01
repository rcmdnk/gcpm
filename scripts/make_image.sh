#!/usr/bin/env bash

name=gcp-wn-template-01
image_name=gcp-wn-image-01

# Check args
HELP="Usage: $(basename "$0") [-n <name>] [-o <output-image>]

Arguments:
-n <name>          Set template machine name (default: $name)
-o <output-image>  Set output image name (default: $image_name)
-h                 Show help

In addition, you can set template machine's settings as follows:
$($(dirname $0)/make_template.sh -h|grep -v "Usage"|grep -v -- "-n"|grep -v -- "-h")
"

options=""
while getopts n:z:p:f:i:m:d:o:h OPT;do
  case $OPT in
    "n" ) name=$OPTARG; options="$options -n $name";;
    "z" ) zone=$OPTARG; options="$options -z $zone";;
    "p" ) image_project=$OPTARG; options="$options -z $image_project";;
    "f" ) image_family=$OPTARG; options="$options -z $image_family";;
    "i" ) image=$OPTARG; options="$options -z $image";;
    "m" ) machine_type=$OPTARG; options="$options -m $machine_type";;
    "d" ) boot_disk_size=$OPTARG; options="$options -d $boot_disk_size" ;;
    "o" ) image_name=$OPTARG;;
    "h" ) echo "$HELP";exit 2;;
    * ) echo "Unknown argument: $OPT";exit 1;;
  esac
done
shift $((OPTIND - 1))

$(dirname $0)/make_template.sh "$@"
ret=$?
if [ $ret -ne 0 ];then
  exit $ret
fi
# Wait 60 sec after instance is started for safe, otherwise image will be broken
echo "Wait 60sec for safe..."
sleep 60

tmpdir=$(mktemp -d)
if [ -z "$tmpdir" ];then
  tmpdir="./.make_image.tmp"
  mkdir $tmpdir
  echo "failing to make temporal directory."
  echo "use $tmpdir"
fi
cd "$tmpdir"
curl -LOkSs   https://github.com/mickaneda/gcp-tools/archive/master.tar.gz
tar xzf master.tar.gz >/dev/null
export PATH=$PATH:gcp-tools-master/bin
gce make_image "$name" "$image_name"
gce rm "$name"
rm -rf "$tmpdir"
