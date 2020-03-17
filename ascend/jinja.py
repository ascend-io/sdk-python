import base64
import os
import json
from google.protobuf.json_format import ParseDict, MessageToJson
from ascend.protos.io import io_pb2

import jinja2


def b64encode(value):
    return base64.b64encode(value.encode('utf-8')).decode()


def dump_json(data):
    return json.dumps(data)


def ascend_include_raw(dir, path):
    with open(os.path.join(dir, path)) as f:
        return f.read()


def construct_immediate_container(dir, files):
    objs = []
    all_data = bytes()
    for file in files:
        with open(f'{dir}/{file}', 'rb') as f:
            data = f.read()
            l = len(data)
            all_data += data
            objs.append({
                'name': file,
                'length': l
            })
    message = io_pb2.Immediate.Container()
    ParseDict({'object': objs, 'content_some': base64.b64encode(all_data).decode()}, message)
    return MessageToJson(message)


def setup_jinja_env(loader):
    jinja_env = jinja2.Environment(loader=loader)
    jinja_env.filters['dumpJson'] = dump_json
    jinja_env.filters['b64encode'] = b64encode
    jinja_env.globals['construct_immediate_container'] = construct_immediate_container
    jinja_env.globals['ascend_include_raw'] = ascend_include_raw
    return jinja_env
