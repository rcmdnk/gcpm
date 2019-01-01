#!/bin/sh

basedir="$(dirname $0)/.."
cp $basedir/bin/gcpm /usr/bin/
echo "/usr/bin/gcpm was installed"
cp $basedir/usr/lib/systemd/system/gcpm.service /usr/lib/systemd/system/
echo "/usr/lib/systemd/system/gcpm.service was installed"
cp $basedir/etc/rsyslog.d/gcpm.conf /etc/rsyslog.d/
systemctl daemon-reload
echo "/etc/rsyslog/gcpm.conf was installed"
systemctl restart rsyslog
cp $basedir/etc/logrotate.d/gcpm.conf /etc/logrotate.d/
echo "/etc/logrotate.d/gcpm.conf was installed"

if [ ! -f /etc/gcpm.conf ];then
  cp $basedir/etc/gcpm.conf /etc/
  echo "/etc/gcpm.conf was installed"
  echo
  echo "Please modify /etc/gcpm.conf for your environment"
  echo
fi

gcloud=($(grep "^gcloud " /etc/gcpm.conf 2>/dev/null))
gcloud=${gcloud[1]:-/root/google-cloud-sdk/bin/gcloud}
if ! type "$gcloud" >/dev/null 2>&1 && ! type gcloud >/dev/null 2>&1;then
  echo "gcloud tool is not installed or not in $gcloud"
  echo "Please install gcloud and/or set path in your configuration file as 'gcloud /path/to/gcloud'"
  echo "Ref: https://cloud.google.com/sdk/install"
fi
