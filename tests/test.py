from ascend.client import Client
from ascend.model import Component

import requests
import subprocess

ENVIRONMENT_PREFIX = "ft-serv-acct-api-keys"

def main():
    access_key = subprocess.run(
        "credstash -t eng get default_service_account_access_key",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable="/bin/bash").stdout.decode('utf-8').strip()
    secret_key = subprocess.run(
        "credstash -t eng get default_service_account_secret_key",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable="/bin/bash").stdout.decode('utf-8').strip()
    ascend_client = Client(access_key, secret_key, ENVIRONMENT_PREFIX)
    ds = ascend_client.data_service("kitchen_sink")

    comp = Component("test", "small_stuff", "sources", "blob", session=ascend_client.get_session())
    print(comp.stream_records())

if __name__ == '__main__':
    main()
