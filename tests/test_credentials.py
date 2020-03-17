import unittest
import ascend.resource_definitions as resource_definitions
import ascend.transforms as transforms
import ascend.credentials as credentials
from google.protobuf.json_format import ParseDict, MessageToDict
from ascend.protos.resource import resource_pb2
import yaml


class TestCredentials(unittest.TestCase):
    creds_file = f'tests/test_credentials_creds.yaml'
    comps_file = f'tests/test_credentials_components.yaml'

    def setUp(self):
        # import ascend.cli.global_values as globals
        # globals.DEBUG = True
        self.maxDiff = None
        self.creds = credentials.load_credentials(self.creds_file)
        with open(self.comps_file) as f:
            raw = yaml.load(f.read(), Loader=yaml.SafeLoader)
        proto = resource_pb2.Resource()
        ParseDict(raw, proto)
        res_def = resource_definitions.ResourceDefinition.from_resource_proto(proto,
                                                                              ('df', 'ds', None))
        self.components = {
            comp.resource_id: comp for comp in res_def.contained()
        }
        for k in self.components.keys():
            name, suff = k.split('.')
            if suff == 'before':
                assert f'{name}.after' in self.components
            elif suff == 'after':
                assert f'{name}.before' in self.components
            elif suff == 'none':
                continue
            else:
                raise ValueError(f'Unexpected suffix {suff}')

    def test_set_creds(self):
        for k, comp in self.components.items():
            name, suff = k.split('.')
            if suff == 'after' or suff == 'none':
                continue
            with self.subTest(f'set creds for {name}'):
                # print(f'before: {comp.rd}')
                try:
                    for transform in comp.transforms:
                        transform.to_api(creds=self.creds)
                except Exception as e:
                    raise Exception(f'Failure to set creds for {comp}') from e
                after_id = f'{name}.after'
                comp.rd['id'] = after_id
                # print(f'after: {comp.rd}')
                # print(f'expected: {self.components[after_id].rd}')
                self.assertDictEqual(comp.rd, self.components[after_id].rd)

    def test_creds_snippet(self):
        m = {}
        for k, comp in self.components.items():
            name, suff = k.split('.')
            with self.subTest(f'get snippet for {name}'):
                # print(f'before: {comp.rd}')
                try:
                    for transform in comp.transforms:
                        if isinstance(transform, transforms.Creds):
                            m = {**m, **transform.snippet()}
                except Exception as e:
                    raise Exception(f'Failure to get snippet for {comp}') from e
        for k, v in self.creds.items():
            self.assertIn(k, m, f'{k} not found, expecting for {v}')
            self.assertEqual(v.credential_id, m[k].credential_id,
                             f'Credential Id mismatch for {v} and {m[k]}')
            self.assertEqual(v.credential_type, m[k].credential_type,
                             f'Credential type mismatch for {v} and {m[k]}')
        dump = credentials.dump_credentials(m)
        self.assertListEqual(yaml.load(dump, Loader=yaml.SafeLoader)['credentials'],
                             sorted([MessageToDict(v.proto) for v in m.values()],
                                    key=lambda v: v['id']['value']))

