#!/usr/bin/env bash

# Check gcloud
if ! type gcloud >& /dev/null;then
  message="gcloud tools are not installed, do you want to install?"
  while : ;do
    echo "$message [y/n]: " >/dev/tty
    read -srn 1 ans </dev/tty
    if [ "$ans" = "y" ];then
      curl https://sdk.cloud.google.com | bash
      echo "Setup gcloud's account"
      exit 2
    elif [ "$ans" = "n" ];then
      err "Intall gcloud: https://cloud.google.com/sdk/install"
      exit 1
    fi
  done
fi
