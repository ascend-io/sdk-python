import base64
import copy
import os
from types import MappingProxyType
from typing import Mapping
from ascend.cli import sh
import ascend.credentials as credentials
from ascend.protos.io import io_pb2
from google.protobuf.json_format import ParseDict


def file_template_prefix(key, file_name):
    return f"""{{%- set {key} = ascend_include_raw(resourceParentDirectory, "{file_name}") %}}\n"""


def file_template_replacement(key, use_base_64 = False):
    return f"""{{{{ {key} | {"b64encode" if use_base_64 else "dumpJson"} }}}}"""


def immediate_prefix(resource_id, files):
    files_string = ", ".join(f'"{f}"' for f in files)
    return f"{{%- set ascendImmediateDir -%}}{{{{ resourceParentDirectory }}}}/{resource_id}{{%- endset %}}\n" +\
        f"{{%- set ascendImmediateFiles = [{files_string}] %}}\n"


class Transform:
    def __init__(self, rd, k, *args, **kwargs):
        self.rd = rd
        self.k = k
        self.prev = copy.deepcopy(rd)

    # transform rd before converting to api resource
    def to_api(self, *args, **kwargs):
        pass

    # transform rd after converting from api resource,
    # return tuple of extra data to be printed before rendering dict as yaml
    # as well as post-processing function to run on rendered yaml
    def from_api(self, *args, **kwargs):
        return None


class SqlQuery(Transform):
    KEY = "ascendSqlStmt"

    def from_api(self, *args, **kwargs):
        if kwargs['directory']:
            parent = kwargs['parent_directory']
            res_def = kwargs['res_def']
            file_name = f'{res_def.resource_id}.sql'
            path = os.path.join(parent, file_name)
            with open(path, 'w') as f:
                f.write(self.prev[self.k])
            self.rd[self.k] = self.KEY
            replacement = file_template_replacement(self.KEY)
            post_process = lambda s: s.replace(self.KEY, replacement)
            return (file_template_prefix(self.KEY, file_name), post_process)
        else:
            return None


class PythonCode(Transform):
    def use_base_64(self):
        raise NotImplementedError(self)

    def key(self):
        raise NotImplementedError(self)

    def from_api(self, *args, **kwargs):
        if kwargs['directory']:
            parent = kwargs['parent_directory']
            res_def = kwargs['res_def']
            file_name = f'{res_def.resource_id}_{self.key()}.py'
            path = os.path.join(parent, file_name)
            with open(path, 'w') as f:
                data = self.prev[self.k]
                if self.use_base_64():
                    data = base64.b64decode(data).decode()
                f.write(data)
            template_key = f'ascend_{self.key()}'
            self.rd[self.k] = template_key
            replacement = file_template_replacement(template_key, self.use_base_64())
            post_process = lambda s: s.replace(template_key, replacement)
            return (file_template_prefix(template_key, file_name), post_process)
        else:
            return None


class ImmediateContainer(Transform):
    def from_api(self, *args, **kwargs):
        if kwargs['directory']:
            parent = kwargs['parent_directory']
            objects = self.prev[self.k]['object']
            res_def = kwargs['res_def']
            content = base64.b64decode(self.prev[self.k]['contentSome'])
            files = []
            offset = 0
            immediate_dir = os.path.join(parent, res_def.resource_id)
            os.makedirs(immediate_dir, exist_ok=True)
            for obj in objects:
                l = int(obj['length'])
                file_content = content[offset:offset+l]
                offset += l
                file = obj['name']
                with open(os.path.join(immediate_dir, file), 'wb') as f:
                    f.write(file_content)
                files.append(file)
            replacement = "{{ construct_immediate_container(ascendImmediateDir, ascendImmediateFiles) }}"
            key = 'ascendImmediateContainer'
            self.rd[self.k] = key
            post_process = lambda s: s.replace(key, replacement)
            return (immediate_prefix(res_def.resource_id, files), post_process)
        else:
            return None


class ByteFunction(PythonCode):
    def key(self):
        return "byte_function"

    def use_base_64(self):
        return True


class LambdaParser(PythonCode):
    def key(self):
        return "lambda_parser"

    def use_base_64(self):
        return True


class PySpark(PythonCode):
    def key(self):
        return "pyspark"

    def use_base_64(self):
        return False


class MapData(Transform):
    def map_to(self, data):
        return data

    def map_from(self, data):
        return data

    def to_api(self, *args, **kwargs):
        self.rd[self.k] = self.map_to(self.rd[self.k])

    def from_api(self, *args, **kwargs):
        self.rd[self.k] = self.map_from(self.rd[self.k])


class Base64(MapData):
    def map_to(self, data):
        return base64.b64encode(bytes(data, 'utf-8'))

    def map_from(self, data):
        return base64.b64decode(data).decode('utf-8')


def apply_creds(cont, typ, cred_id, creds):
    sh.debug(f'apply cred: {cred_id}')
    if cred_id in creds:
        cred = creds[cred_id]
        if cred.credential_type != typ:
            raise ValueError(f'Wrong type for {cred_id} '
                             f'(expected {typ}, but found {cred.credential_type})')
        cont['credentials'] = cred.credential_value
    else:
        sh.debug(f'{cred_id} not found in creds')


class Creds(Transform):
    def snippet(self) -> Mapping[str, credentials.Credential]:
        raise NotImplementedError(self)

    def set_creds(self, rd, creds):
        raise NotImplementedError(self)

    def convert_to_name(self, rd, translate_cred):
        raise NotImplementedError(self)

    def to_api(self, *args, **kwargs):
        creds = kwargs['creds']
        self.set_creds(self.rd[self.k], creds)

    def from_api(self, *args, **kwargs):
        translate_cred = kwargs['translate_cred']
        self.convert_to_name(self.rd[self.k], translate_cred)


class BasicCreds(Creds):
    def cred_type(self):
        raise NotImplementedError(self)

    def snippet(self):
        return self._snippet({}, self.cred_type(), self.rd[self.k])

    def _snippet(self, result, typ, rd, staging=False):
        cred_id = rd.get('credentialId')
        if cred_id is not None:
            cred = io_pb2.Credentials()
            d = {
                'id': cred_id,
                typ: rd.get('credentials')
            }
            ParseDict(d, cred)
            result[cred_id['value']] = credentials.Credential(cred)
        if not staging and self.staging_type() is not None:
            self._snippet(result, self.staging_type(), rd['stagingContainer'], staging=True)
        return result

    def staging_type(self):
        return None

    def set_creds(self, rd, creds):
        self._set_creds(rd, self.cred_type(), creds)

    def convert_to_name(self, rd, translate_cred):
        cred_id_to_name(rd, translate_cred, self.staging_type())

    def _set_creds(self, rd, typ, creds, staging=False):
        cred_id = rd.get('credentialId', None)
        if cred_id is not None:
            v = cred_id['value']
            apply_creds(rd, typ, v, creds)
            if not staging and self.staging_type() is not None:
                self._set_creds(rd['stagingContainer'], self.staging_type(), creds, staging=True)
        else:
            sh.debug(f'no credentialId for {rd}')


class AzureCreds(BasicCreds):
    def cred_type(self):
        return 'azure'


class GcpCreds(BasicCreds):
    def cred_type(self):
        return 'gcp'


class BqCreds(GcpCreds):
    def staging_type(self):
        return 'gcp'


class MySqlCreds(BasicCreds):
    def cred_type(self):
        return 'mysql'


class S3Creds(BasicCreds):
    def cred_type(self):
        return 'aws'


class RedshiftCreds(BasicCreds):
    def cred_type(self):
        return 'redshift'

    def staging_type(self):
        return 'aws'


def cred_id_to_name(rd, translate_cred, staging_type=None):
    rd['credentialId']['value'] = translate_cred(rd['credentialId']['value'])
    if staging_type is not None:
        cred_id_to_name(rd['stagingContainer'], translate_cred)


class FunctionCreds(Creds):
    def snippet(self):
        result = {}
        config = self.rd[self.k].get('credentialsConfiguration')
        if config is not None:
            cred_id = config['id']
            cred = io_pb2.Credentials()
            d = {
                'id': cred_id,
                'function': config.get('credentials')
            }
            ParseDict(d, cred)
            result[cred_id['value']] = credentials.Credential(cred)
        return result

    def convert_to_name(self, rd, translate_cred):
        config = self.rd.get('credentialsConfiguration')
        config['id']['value'] = translate_cred(config['id']['value'])

    def set_creds(self, rd, creds):
        config = rd.get('credentialsConfiguration')
        if config is not None:
            cred_id = config['id']['value']
            apply_creds(config, 'function', cred_id, creds)
        else:
            sh.debug(f'no credential config for {rd}')


class StagedCreds(Creds):
    staging_reg = {
        's3': S3Creds,
        'gcs': GcpCreds,
        'abs': AzureCreds
    }

    def staging_type(self, rd):
        return (set(self.staging_reg.keys()) & set(rd.keys())).pop()

    def cred_type(self):
        raise NotImplementedError(self)

    def snippet(self) -> Mapping[str, credentials.Credential]:
        rd = self.rd[self.k]
        cred_id = rd.get('credentialId')
        result = {}
        if cred_id:
            d = {
                'id': cred_id,
                self.cred_type(): rd.get('credentials')
            }
            cred = io_pb2.Credentials()
            ParseDict(d, cred)
            result[cred_id['value']] = credentials.Credential(cred)
        staging_type = self.staging_type(rd)
        staging_creds = self.staging_reg[staging_type](rd, staging_type)
        staging_result = staging_creds.snippet()
        return {**result, **staging_result}

    def convert_to_name(self, rd, translate_cred):
        cred_id_to_name(rd, translate_cred)
        cred_id_to_name(rd[self.staging_type], translate_cred)

    def set_creds(self, rd, creds):
        id = rd.get('credentialId')
        if id is not None:
            cred_id = id['value']
            apply_creds(rd, self.cred_type(), cred_id, creds)
            staging_type = self.staging_type(rd)
            staging_creds = self.staging_reg[staging_type](rd, staging_type)
            staging_creds.set_creds(rd[staging_type], creds)
        else:
            sh.debug(f'no credentialId for {rd}')


class SnowflakeCreds(StagedCreds):
    def cred_type(self):
        return 'snowflake'


class MsSqlServerCreds(StagedCreds):
    def cred_type(self):
        return 'ms_sql_server'


class PopulateUpdatePeriodical(MapData):
    def map_from(self, data):
        if data.get('updatePeriodical', {}) == {}:
            default = {'offset': '103366736s', 'period': '134217727s'}
            data['updatePeriodical'] = default
        return data


TRANSFORM_KEY = 'TRANSFORM'

ContainerTransforms = MappingProxyType({
    'abs': {
        TRANSFORM_KEY: AzureCreds,
    },
    'bigQuery': {
        TRANSFORM_KEY:  BqCreds,
    },
    'byteFunction': {
        'container': {
            TRANSFORM_KEY: FunctionCreds,
            'executable': {
                'code': {
                    'source': {
                        'inline': {
                            TRANSFORM_KEY: ByteFunction
                        },
                    },
                },
            },
        },
    },
    'gcs': {
        TRANSFORM_KEY: GcpCreds,
    },
    'immediate': {
        TRANSFORM_KEY: ImmediateContainer,
    },
    'msSqlServer': {
        TRANSFORM_KEY: MsSqlServerCreds,
    },
    'mysql': {
        TRANSFORM_KEY: MySqlCreds,
    },
    'mysqlPartition': {
        TRANSFORM_KEY: MySqlCreds
    },
    'redshift': {
        TRANSFORM_KEY: RedshiftCreds,
    },
    's3': {
        TRANSFORM_KEY: S3Creds,
    },
    'recordFunction': {
        'container': {
            TRANSFORM_KEY: FunctionCreds,
        },
    },
    'snowflake': {
        TRANSFORM_KEY: SnowflakeCreds
    },
})

OperatorTransforms = MappingProxyType({
    'sparkFunction': {
        TRANSFORM_KEY: FunctionCreds,
        'executable': {
            'code': {
                'source': {
                    'inline': {
                        TRANSFORM_KEY: PySpark
                    },
                },
            },
        },
    },
    'sqlQuery': {
        'sql': {
            TRANSFORM_KEY: SqlQuery
        }
    }
})

ComponentTransforms = MappingProxyType({
    'readConnector': {
        'container': ContainerTransforms,
        'bytes': {
            'parser': {
                'lambdaParser': {
                    'code': {
                        'inline': {
                            TRANSFORM_KEY: LambdaParser
                        },
                    },
                },
            },
        },
        TRANSFORM_KEY: PopulateUpdatePeriodical,
    },
    'transform': {
        'operator': OperatorTransforms,
    },
    'writeConnector': {
        'container': ContainerTransforms,
    },
})


class Transforms:
    TRANSFORM_REGISTRY = MappingProxyType({
        'component': ComponentTransforms
    })

    @staticmethod
    def from_rd(rd: dict):
        """
        :param rd: dict corresponding to resource proto
        :return: list of transforms on this resource definition data
        """
        transforms = []

        def recur(rest: dict, reg):
            matches = set(rest.keys()) & set(reg.keys())
            for match in matches:
                next_reg = reg.get(match, {})
                good = False
                if TRANSFORM_KEY in next_reg:
                    transforms.append(next_reg.get(TRANSFORM_KEY)(rest, match))
                    good = True
                if isinstance(next_reg, Mapping) and isinstance(rest[match], Mapping):
                    recur(rest[match], next_reg)
                    good = True
                if not good:
                    raise Exception(f"Unexpected registration: {next_reg}")
        recur(rd, Transforms.TRANSFORM_REGISTRY)
        return transforms

