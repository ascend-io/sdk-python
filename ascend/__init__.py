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

feeds = A.list_datafeeds()

df = pd.DataFrame.from_records(feeds[0].get_records())
"""

import yaml


# format newlines nicely in yaml
def _yaml_str_format(dumper: yaml.Dumper, s: str):
    if '\n' in s:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', s, style='|')
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', s)


yaml.add_representer(str, _yaml_str_format)
