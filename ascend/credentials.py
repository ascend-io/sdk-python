from ascend.cli import sh
from dataclasses import dataclass
from ascend.protos.io import io_pb2
from ascend.protos.resource import resource_pb2
from ascend.util import coalesce
from google.protobuf.json_format import MessageToDict, ParseDict
from typing import Mapping, Optional
import os
import yaml


class BadCredentialsFile(ValueError):
    pass


def load_credentials(override_path: Optional[str]) -> Mapping[str, 'Credential']:
    path = override_path
    if path is None:
        path = '~/.ascend/component-credentials.yaml'
    path = os.path.expanduser(path)
    proto = resource_pb2.Credentials()
    result = {}
    with open(path) as f:
        data = f.read()
        try:
            d = yaml.load(data, Loader=yaml.SafeLoader)
            ParseDict(d, proto)
            for cred in proto.credentials:
                result[cred.id.value] = Credential(proto=cred, name=cred.id.value)
        except Exception as e:
            raise BadCredentialsFile(path) from e
    sh.debug(f'Loaded {len(d)} credentials from {path}')
    return result


def dump_credentials(d: Mapping[str, 'Credential']):
    if len(d) > 0:
        creds = sorted((v for v in d.values()), key=lambda v: v.credential_id)
        proto = resource_pb2.Credentials(credentials=[c.proto for c in creds])
        return yaml.dump(MessageToDict(proto, including_default_value_fields=True))
    else:
        return ''


@dataclass
class Credential:
    proto: io_pb2.Credentials
    name: str

    @property
    def credential_id(self):
        return self.proto.id.value

    def create_payload(self):
        inner = {
            **MessageToDict(self.proto)
        }
        del inner['id']
        return {
            'credential': inner,
            'name': self.name,
        }

    @staticmethod
    def from_entry(entry):
        name = entry.get('name')
        proto = io_pb2.Credentials
        ParseDict(entry.get('credential'), proto)
        return Credential(proto=proto, name=name)

    @property
    def credential_type(self):
        return self.proto.WhichOneof('details')

    @property
    def credential_value(self):
        return MessageToDict(getattr(self.proto, self.credential_type))
