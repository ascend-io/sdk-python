import copy
import os
import shutil
import unittest
import yaml
import ascend.jinja as jinja
from protos.resource import resource_pb2
from ascend.resource_definitions import ResourceDefinition
from google.protobuf.json_format import ParseDict, MessageToDict
import jinja2


class TestTemplates(unittest.TestCase):
    TEMPLATES = "tests/test_templates.yaml"
    SQL_TEMPLATE = "tests/test_sql_template.yaml"
    CONFIG = "tests/test_template_config.yaml"
    TEMPLATE_PRODUCE = "tests/template_produce"
    DEST = "tests/template_produce/results"
    EXPECT = "tests/expected"

    def setUp(self):
        os.makedirs(self.DEST, exist_ok=True)
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.DEST)
        pass

    def test_immediate_template_render(self):
        env = jinja.setup_jinja_env(loader=jinja2.FileSystemLoader("tests"))
        with open(self.CONFIG) as f:
            config = yaml.load(f.read(), Loader=yaml.SafeLoader)
        with open(self.TEMPLATES) as f:
            raw_data = f.read()
        rendered = env.from_string(raw_data).render(config=config, resourceParentDirectory="tests")
        # print(rendered)
        data = yaml.load(rendered, Loader=yaml.SafeLoader)
        # print(data)
        dataflow = resource_pb2.Dataflow()
        ParseDict(data, dataflow)
        self.dataflow_assert(dataflow)

    def dataflow_assert(self, dataflow):
        comps = {}
        for component in dataflow.components:
            orig_id = component.id
            d = MessageToDict(component)
            del d['id']
            comps[orig_id] = d
        for id, comp in comps.items():
            name, suff = id.split('.')
            if suff == 'from':
                self.assertDictEqual(comp, comps[f'{name}.to'])

    def test_sql_template_render(self):
        env = jinja.setup_jinja_env(loader=jinja2.FileSystemLoader("tests"))
        with open(self.CONFIG) as f:
            config = yaml.load(f.read(), Loader=yaml.SafeLoader)
        with open(self.SQL_TEMPLATE) as f:
            raw_data = f.read()
        rendered = env.from_string(raw_data).render(config=config, resourceParentDirectory="tests")
        # print(rendered)
        data = yaml.load(rendered, Loader=yaml.SafeLoader)
        # print(data)
        resource = resource_pb2.Resource()
        ParseDict(data, resource)
        self.dataflow_assert(resource.dataflow)

    def template_produce(self, resource_id):
        env = jinja.setup_jinja_env(loader=jinja2.FileSystemLoader("tests"))
        with open(os.path.join(self.TEMPLATE_PRODUCE, f"{resource_id}.yaml")) as f:
            raw_data = f.read()
        d = yaml.load(raw_data, Loader=yaml.SafeLoader)
        res_proto = resource_pb2.Resource()
        ParseDict(d, res_proto)
        res_def = ResourceDefinition.from_resource_proto(res_proto, ('ds', 'df', resource_id))
        initial_rd = copy.deepcopy(res_def.rd)
        path = os.path.join(self.DEST, f"{resource_id}.yaml")
        res_def.do_dump(path, directory=True)

        # round trip compare
        with open(path, 'r') as f:
            re_raw_data = f.read()
        rendered = env.from_string(re_raw_data).render(config={}, resourceParentDirectory=self.DEST)
        # print(rendered)
        d = yaml.load(rendered, Loader=yaml.SafeLoader)
        re_read = resource_pb2.Resource()
        ParseDict(d, re_read)
        roundtripped = ResourceDefinition.from_resource_proto(re_read, ('ds', 'df', resource_id))
        self.assertDictEqual(roundtripped.rd, initial_rd)

        # expected compare
        with open(os.path.join(self.EXPECT, f"{resource_id}.yaml")) as f:
            expect_raw = f.read()
        res_proto = resource_pb2.Resource()
        ParseDict(d, res_proto)
        expected = ResourceDefinition.from_resource_proto(re_read, ('ds', 'df', resource_id))
        self.assertDictEqual(expected.rd, initial_rd)


    def test_template_produce(self):
        self.template_produce("immediate1")
        self.template_produce("immediate2")
        self.template_produce("sql")
        self.template_produce("pyspark")
        self.template_produce("crc")


