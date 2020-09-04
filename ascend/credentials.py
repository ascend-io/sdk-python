from ascend.cli import sh
from dataclasses import dataclass
from ascend.protos.io import io_pb2
from ascend.protos.resource import resource_pb2
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
                result[cred.id.value] = Credential(cred)
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

    @property
    def credential_id(self):
        return self.proto.id.value

    @property
    def credential_type(self):
        return self.proto.WhichOneof('details')

    @property
    def credential_value(self):
        return MessageToDict(getattr(self.proto, self.credential_type))


@dataclass
class CredentialEntry:
    proto: resource_pb2.CredentialEntry

    @property
    def credential(self):
        return Credential(proto=self.proto.credential)

    @property
    def name(self):
        return self.proto.name

    def get_creation_payload(self):
        d = MessageToDict(self.proto)
        if d.get('credential', {}).get('id') is not None:
            del d['credential']['id']
        return d

    @staticmethod
    def from_credential(cred: Credential, name: str):
        d = {
            'credential': MessageToDict(cred.proto),
            'name': name
        }
        proto = resource_pb2.CredentialEntry()
        ParseDict(d, proto)
        return CredentialEntry(proto)

    @staticmethod
    def from_json(payload):
        proto = resource_pb2.CredentialEntry()
        ParseDict(payload, proto, ignore_unknown_fields=True)
        return CredentialEntry(proto=proto)
