"""
Ascend Util module

Some frequently-used Helper functions
"""

import hashlib
import hmac

type_names = {
    'source': 'ReadConnector',
    'sink': 'WriteConnector',
    'view': 'Transform',
    'sub': 'DataFeedConnector',
    'pub': 'DataFeed'
}


def sign(signing_key, msg):
    return hmac.new(signing_key, msg.encode('utf-8'), hashlib.sha256).digest()


def create_signature_key(signing_key, timestamp, region, service):
    signature = sign(('AWS4' + signing_key).encode('utf-8'), timestamp)
    signature = sign(signature, region)
    signature = sign(signature, service)
    signature = sign(signature, 'aws4_request')
    return signature


def parse_component_type(component_json):
    k = component_json.get('type', None)
    if k is not None:
        return k
    for k in component_json.keys():
        if k in type_names:
            return k
    return ""


def display_type_name(typ):
    return type_names.get(typ, 'UnknownComponent({})'.format(typ))
