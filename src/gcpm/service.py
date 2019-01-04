# -*- coding: utf-8 -*-

"""
    Module to provide google service management
"""

import os
import sys
from .utils import expand
from __init__ import __version__
from __init__ import __program__
import httplib2
from google.oauth2 import service_account
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from oauth2client.tools import argparser
from oauth2client.client import OAuth2WebServerFlow
from apiclient.discovery import build

__CLIENT_ID__ =\
    "154689602688-rmimpcfc5d5th2nb2rbap02sujh0ehtg.apps.googleusercontent.com"
__CLIENT_SECRET__ = "LouXW0cr1pkCoi8QtTOweld2"


def service_from_oauth(oauth_file, api_name, api_version, scope):
    oauth_file = expand(oauth_file)
    oauth_dir = os.path.dirname(oauth_file)
    if not os.path.isdir(oauth_dir):
        os.makedirs(oauth_dir)
    storage = Storage(oauth_file)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        args, unknown = argparser.parse_known_args(sys.argv)
        credentials = run_flow(
            OAuth2WebServerFlow(
                client_id=__CLIENT_ID__,
                client_secret=__CLIENT_SECRET__,
                scope=scope,
                user_agent=__program__ + '/' + __version__),
            storage, args)

    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build(api_name, api_version, http=http, cache_discovery=False)
    return service


def service_from_service_account(
        service_account_file, api_name, api_version, scope):
    f = expand(service_account_file)
    credentials = service_account.Credentials.from_service_account_file(
        f, scopes=scope)
    service = build(api_name, api_version,
                    credentials=credentials)
    return service


def get_service(service_account_file="",
                oauth_file="~/.config/gcpm/oauth",
                scope=["https://www.googleapis.com/auth/cloud-platform"],
                api_name="compute",
                api_version="v1"):
    if service_account_file == "":
        service = service_from_oauth(
            oauth_file=oauth_file, api_name=api_name, api_version=api_version,
            scope=scope)
    else:
        service = service_from_service_account(
            service_account_file=service_account_file,
            api_name=api_name, api_version=api_version, scope=scope)
    return service


def get_compute(service_account_file="",
                oauth_file="~/.config/gcpm/oauth"):
    return get_service(service_account_file=service_account_file,
                       oauth_file=oauth_file,
                       scope=[
                           "https://www.googleapis.com/auth/compute"
                       ],
                       api_name="compute",
                       api_version="v1")


def get_storage(service_account_file="",
                oauth_file="~/.config/gcpm/oauth"):
    return get_service(service_account_file=service_account_file,
                       oauth_file=oauth_file,
                       scope=[
                           "https://www.googleapis.com/auth/cloud-platform"
                       ],
                       api_name="storage",
                       api_version="v1")
