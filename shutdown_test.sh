#!/usr/bin/env bash
preempted=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/preempted" -H "Metadata-Flavor: Google")
echo "{\"date\": \"$(date +%s)\", \"preempted\": ${preempted}}" >>/var/log/shutdown.log