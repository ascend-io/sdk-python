"""
Ascend SDK for Python

## Modules
* [ascend.client](./client.md) manages connections between SDK clients and the Ascend host.
* [ascend.model](./model.md) provides model classes for finding and manipulating resources in Ascend.

## Typical Usage

```
from ascend.client import Client
import configparser
import os
import pandas as pd

profile = "trial"
host = "trial.ascend.io"

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.ascend/credentials"))

access_id = config.get(profile, "ascend_access_key_id")
secret_key = config.get(profile, "ascend_secret_access_key")

A = Client(host, access_id, secret_key)

feeds = A.list_data_feeds()

df = pd.DataFrame.from_records(feeds[0].get_records())
"""
