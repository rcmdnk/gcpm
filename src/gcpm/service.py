import os
import googleapiclient.discovery
from google.oauth2 import service_account


def service(
        service_account_file,
        scopes=['https://www.googleapis.com/auth/cloud-platform']):
    f = os.path.expandvars(os.path.expanduser(service_account_file))
    credentials = service_account.Credentials.from_service_account_file(
        f, scopes=scopes)
    service = ""
    return service
