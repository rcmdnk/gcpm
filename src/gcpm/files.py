# -*- coding: utf-8 -*-

"""
    Module to mange Google Cloud Storage.
"""


import os
from .utils import expand, proc


__SERVICE_FILE__ = "/usr/lib/systemd/system/gcpm.service"
__LOGROTATE_FILE__ = "/etc/logrotate.d/gcpm.conf"


def make_file(filename, content="", mkdir=True):
    filename = expand(filename)
    directory = os.path.dirname(filename)
    if not os.path.isdir(directory):
        if mkdir:
            os.makedirs(directory)
        else:
            return False
    with open(filename, mode='w') as f:
            f.write(content)
    return True


def rm_file(filename):
    if not os.path.isfile(filename):
        return
    os.remove(filename)


def make_service(filename=__SERVICE_FILE__, mkdir=True):
    content = """[Unit]
Description = HTCondor pool manager for Google Cloud Platform

[Service]
Environment = "PATH={path}"
ExecStart = /usr/bin/gcpm service
ExecStop = /usr/bin/kill -p $MAINPID
Restart = always
StandardOutput = journal
StandardError = journal
SyslogIdentifier = gcpm

[Install]
WantedBy = multi-user.target""".format(path=os.environ["PATH"])
    make_file(filename, content, mkdir)
    proc(["systemctl", "daemon-reload"])


def rm_service(filename=__SERVICE_FILE__):
    rm_file(filename)


def make_logrotate(filename=__LOGROTATE_FILE__, mkdir=True):
    content = """/var/log/gcpm.log {{
  missingok
  rotate 10
  dateext
  delaycompress
  daily
  minsize 100M
  postrotate
      systemctl restart gcpm
  endscript
}}""".format()
    make_file(filename, content, mkdir)


def rm_logrotate(filename=__LOGROTATE_FILE__):
    rm_file(filename)
