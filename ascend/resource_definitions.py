from collections import defaultdict
import ascend.cli.sh as sh
import ascend.cli.global_values as global_values
import ascend.jinja as jinja
from google.protobuf.json_format import MessageToDict, Parse, ParseDict
from protos.resource import resource_pb2
import ascend.credentials
import ascend.model as model
import ascend.transforms as transforms
from ascend.resource import Resource, Component
from ascend.util import filter_none, flatten
import abc
import networkx as nx
from typing import List, Optional, Tuple, Union
import os
import sys
import yaml
from dataclasses import dataclass
import jinja2


ROOT_PATH = (None, None, None)


class ResourceDefinition:
    def __init__(self, resource, resource_type, resource_id):
        self.resource = MessageToDict(resource)
        self.transforms = transforms.Transforms.from_rd(self.resource)
        self.rd = self.resource[resource_type]
        self.resource_name = coalesce(self.resource.get('name'), self.rd.get('name'))
        self.resource_desc = coalesce(self.resource.get('description'), self.rd.get('description'))
        self.resource_id = coalesce(resource_id, self.resource.get('id'), self.rd.get('id'))
        if self.resource_id is None:
            raise ValueError(f"Illegal resource, missing id: {self.resource}")
        self.exportable = True

    @property
    def path(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        raise NotImplementedError(self)

    def dir_path(self, origin_path: 'ResourcePath', target: str):
        '''
        when a target path is provided, it should override the root-level
        resource id, based on the origin resource path.
        '''
        return resolve_path(target, origin_path, self.path)

    @property
    def name(self):
        return self.rd.get('name') or self.resource.get('name')

    @property
    def description(self):
        return self.resource.get('description') or self.rd.get('description', '')

    def dependencies(self):
        raise NotImplementedError(self)

    def delete_deps(self):
        return []

    def dependees(self):
        return []

    def apply_inputs(self, rs: 'ResourceSession'):
        pass

    @staticmethod
    def from_resource_proto(m: resource_pb2.Resource, override_path=(None, None, None)) -> 'ResourceDefinition':
        if m.version > global_values.API_VERSION:
            raise ValueError(f'Version out of date (found {m.version}, '
                             f'running {global_values.API_VERSION})')
        sh.debug(m)
        t = m.WhichOneof('type')
        typed_resource = getattr(m, t)
        if isinstance(typed_resource, resource_pb2.DataService):
            resource = DataServiceDef(m, override_path)
        elif isinstance(typed_resource, resource_pb2.Dataflow):
            resource = DataflowDef(m, override_path)
        elif isinstance(typed_resource, resource_pb2.Component):
            resource = ComponentDef(m, override_path)
        elif isinstance(typed_resource, resource_pb2.Group):
            resource = GroupDef(m, override_path)
        elif isinstance(typed_resource, resource_pb2.DataFeed):
            resource = DataFeedDef(m, override_path)
        else:
            raise KeyError(f"Unrecognizable resource {m}")
        return resource

    # need to hit the api to generate the resource(s) for a definition
    # garuanteed to have dependencies resolve inside rs maps
    def to_resource(self, rs: 'ResourceSession') -> Resource:
        json = {}
        json['id'] = self.resource_id
        json['name'] = self.name
        json['description'] = self.description
        return self.make_resource(json, rs)

    @abc.abstractmethod
    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        pass

    def list(self):
        pass

    def apply(self, rs: 'ResourceSession') -> Resource:
        res = self.to_resource(rs)
        res.apply()
        return res

    def delete(self):
        pass

    def all_transforms(self):
        return self.transforms + flatten(child.transforms for child in self.contained())

    def dump(self, origin, options):
        if not self.exportable:
            return
        target = self.get_dump_target(origin, options)
        self.do_dump(target, options.directory)

    def do_dump(self, target: Optional[str], directory):
        cleanup = []
        self.rd.pop('id', None)
        self.resource.pop('id', None)
        parent_dir = None
        if target is not None:
            parent_dir, _ = os.path.split(target)
        fns = filter_none([t.from_api(
            directory=directory,
            parent_directory=parent_dir,
            res_def=self) for t in self.transforms])
        if len(fns) > 0:
            prefixes, post_fns = zip(*fns)
        else:
            prefixes, post_fns = [], []
        try:
            if target is not None:
                f = open(target, mode='w')
                cleanup.append(f.close)
            else:
                f = sys.stdout
            f.write(f'# id: {self.resource_id}\n')
            f.writelines(sorted(prefixes))
            yaml_data = yaml.dump(self.resource, default_flow_style=False)
            for post_fn in post_fns:
                if post_fn is not None:
                    yaml_data = post_fn(yaml_data)
            f.write(yaml_data)
        finally:
            for c in cleanup:
                c()

    def contained(self) -> List['ResourceDefinition']:
        return []

    def get_dump_target(self, origin_path: 'ResourcePath', options) -> Optional[str]:
        if options.directory is None:
            return options.output
        base_path = options.output
        dirs, t = os.path.split(base_path)
        if t == "" and origin_path.rd_path[0] is not None:
            t = origin_path.resource.resource_id
        suff = self.dir_path(origin_path.rd_path, t) + '.yaml'
        target = os.path.join(dirs, suff)
        sh.debug(f'target for {self.path}: {target}')
        os.makedirs(os.path.split(target)[0], exist_ok=True)
        return target

    def __repr__(self):
        return f'<{type(self)}>: {self.resource_id}'


class ComponentDetailsDef(abc.ABC):
    def __init__(self, rd, comp_def):
        self.rd = rd
        self.comp_def = comp_def

    def input_ids(self):
        return []

    @property
    @abc.abstractmethod
    def api_type(self):
        pass

    @abc.abstractmethod
    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        pass


class ReadConnectorDef(ComponentDetailsDef):
    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        proto = resource_pb2.Component()
        ParseDict(self.comp_def.rd, proto, ignore_unknown_fields=True)
        json['source'] = MessageToDict(proto.read_connector, preserving_proto_field_name=True)
        return model.ReadConnector(self.comp_def.data_service_id, self.comp_def.dataflow_id,
                                   self.comp_def.resource_id, json, rs.session)

    def api_type(self):
        return 'source'


class TransformDef(ComponentDetailsDef):
    def input_ids(self):
        return self.rd['inputIds']

    def api_type(self):
        return 'view'

    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        input_components = [
            self.comp_def.resolve_input(rs, input_id)
            for input_id in self.input_ids()
        ]
        json['inputs'] =[{'uuid': input.uuid, 'type': input.api_type} for input in input_components]
        proto = resource_pb2.Component()
        ParseDict(self.comp_def.rd, proto, ignore_unknown_fields=True)
        json['view'] = MessageToDict(proto.transform, preserving_proto_field_name=True)
        return model.Transform(self.comp_def.data_service_id, self.comp_def.dataflow_id,
                               self.comp_def.resource_id, json, rs.session)


class WriteConnectorDef(ComponentDetailsDef):
    def input_ids(self):
        return [self.rd['inputId']]

    def api_type(self):
        return 'sink'

    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        input = self.comp_def.resolve_input(rs, next(iter(self.input_ids())))
        json['inputType'] = input.api_type
        json['inputUUID'] = input.uuid
        proto = resource_pb2.Component()
        ParseDict(self.comp_def.rd, proto, ignore_unknown_fields=True)
        json['sink'] = MessageToDict(proto.write_connector, preserving_proto_field_name=True)
        return model.WriteConnector(self.comp_def.data_service_id, self.comp_def.dataflow_id,
                                    self.comp_def.resource_id, json, rs.session)


class DataFeedDef(ResourceDefinition):
    def __init__(self, resource: resource_pb2.Resource, override_path):
        self.data_service_id, resource_id, _ = override_path
        super().__init__(resource, 'dataFeed', resource_id)
        self.dataflow_id, self.input_id = self.rd['inputId'].split('.')
        self.exportable = False

    @property
    def path(self):
        return (self.data_service_id, self.resource_id, None)

    def dependees(self):
        if self.rd.get('groupId') is not None:
            return [(self.data_service_id, self.dataflow_id, self.rd['groupId'])]
        else:
            return []

    def dependencies(self):
        return [(self.data_service_id, self.dataflow_id, self.input_id)]

    def api_type(self):
        return 'pub'

    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        input = rs.get_resource(self.data_service_id, self.dataflow_id, self.input_id)
        json['inputType'] = input.api_type
        json['inputUUID'] = input.uuid
        proto = resource_pb2.DataFeed()
        ParseDict(self.rd, proto)
        if proto.group_id != '':
            group_path = (self.data_service_id, self.dataflow_id, proto.group_id)
        else:
            group_path = None
        rs.update_group(group_path, self.path)
        if proto.sharing.all:
            json['open'] = True
            json['pubToRoles'] = ""
        else:
            json['open'] = False
            ds_ids = proto.sharing.data_services
            shared_roles = []
            for ds_id in ds_ids:
                try:
                    orgUUID = rs.get_ds(ds_id).uuid
                except KeyError:
                    # do not have this org
                    sh.debug(f'cannot get uuid for {ds_id}')
                    continue
                everyone_role = next(r for r in rs.roles if r['orgId'] == orgUUID and r['id'] == 'Everyone')
                shared_roles.append(everyone_role['uuid'])
            if not proto.sharing.hidden:
                host_ds = rs.get_resource(self.data_service_id, None, None)
                everyone_role = next(r for r in rs.roles if r['orgId'] == host_ds.uuid and r['id'] == 'Everyone')
                shared_roles.append(everyone_role['uuid'])
            json['pubToRoles'] = ','.join(shared_roles)
        return model.DataFeed(
            self.data_service_id, self.dataflow_id, self.resource_id, json, rs.session)


class GroupDef(ResourceDefinition):
    def __init__(self, resource: resource_pb2.Resource, override_path):
        self.data_service_id, self.dataflow_id, resource_id = override_path
        super().__init__(resource, 'group', resource_id)
        self.exportable = False

    @property
    def api_type(self):
        return 'group'

    def apply(self, rs: 'ResourceSession') -> Resource:
        try:
            old = rs.get_resource(*self.path)
            prev_uuids = [i['uuid'] for i in old.json_definition['content']]
        except KeyError:
            prev_uuids = []
        sh.debug(f'prev: {prev_uuids}')
        cur_rds = rs.group_path_to_content_path.get(self.path, [])
        cur_uuids = [rs.get_resource(*p).uuid for p in cur_rds]
        sh.debug(f'cur: {cur_uuids}')
        ress = [rs.uuid_to_resource[uuid] for uuid in cur_uuids]
        json = {}
        json['id'] = self.resource_id
        json['name'] = self.rd['name']
        json['description'] = self.rd.get('description', '')
        json['content'] = [{'uuid': res.uuid, 'type': res.api_type} for res in ress]
        sh.debug(json)
        res = model.Group(self.data_service_id, self.dataflow_id, self.resource_id, json, rs.session)
        res.apply()
        return res

    def dependencies(self):
        return [(self.data_service_id, self.dataflow_id, None)]

    @property
    def path(self):
        return (self.data_service_id, self.dataflow_id, self.resource_id)

    @property
    def api_path(self):
        return '/'.join([
            self.data_service_id, self.dataflow_id, self.api_type, self.resource_id
        ])


class ComponentDef(ResourceDefinition):
    TYPES = {
        'readConnector': ReadConnectorDef,
        'transform': TransformDef,
        'writeConnector': WriteConnectorDef,
    }

    def __init__(self, resource: resource_pb2.Resource, override_path):
        self.data_service_id, self.dataflow_id, resource_id = override_path
        super().__init__(resource, 'component', resource_id)
        self.type, = filter(lambda t: t in self.rd, ComponentDef.TYPES)
        self.details = ComponentDef.TYPES[self.type](self.rd[self.type], self)

    def dependees(self):
        if self.rd.get('groupId') is not None:
            return [(self.data_service_id, self.dataflow_id, self.rd['groupId'])]
        else:
            return []

    @property
    def path(self):
        return (self.data_service_id, self.dataflow_id, self.resource_id)

    def apply(self, rs: 'ResourceSession') -> Resource:
        res = self.to_resource(rs)
        res.apply()
        if self.rd.get('groupId') is not None:
            group_path = (self.data_service_id, self.dataflow_id, self.rd['groupId'])
        else:
            group_path = None
        rs.update_group(group_path, self.path)
        return res

    @property
    def api_path(self):
        return '/'.join([
            self.data_service_id, self.dataflow_id, self.details.api_type, self.resource_id
        ])

    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        return self.details.make_resource(json, rs)

    def resolve_input(self, rs: 'ResourceSession', input_id: str) -> 'Resource':
        if '.' not in input_id:
            return rs.get_resource(self.data_service_id, self.dataflow_id, input_id)
        else:
            pub_ds, pub_id = input_id.split('.')
            pub = rs.get_resource(pub_ds, pub_id, None)
            # need to either find a sub for the desired pub, or generate a new one
            sub_uuid = next((v for k, v in rs.type_to_api_path_to_uuid['sub'].items()
                             if k[1] == self.dataflow_id
                             and k[0] == self.data_service_id
                             and rs.uuid_to_resource[v].json_definition['pubUUID'] == pub.uuid),
                            None)
            if sub_uuid is None:
                sub_id = f'sub_for_{pub_id}'
                json = {'id': sub_id, 'name': sub_id,
                        'description': 'Auto-generated sub', 'pubUUID': pub.uuid}
                sub = model.DataFeedConnector(self.data_service_id, self.dataflow_id,
                                              sub_id, json, rs.session)
                sub.apply()
            else:
                sub = rs.uuid_to_resource[sub_uuid]
            return sub

    def dependencies(self):
        inputs = []
        for input_id in self.details.input_ids():
            pieces = input_id.split('.')
            if len(pieces) == 2:
                # data feed reference
                inputs.append((*pieces, None))
            elif len(pieces) == 1:
                # normal
                inputs.append((self.data_service_id, self.dataflow_id, pieces[0]))
            else:
                raise Exception(f'Invalid id format: {input_id} for {self.resource_id}')
        return inputs + [
            (self.data_service_id, None, None),
            (self.data_service_id, self.dataflow_id, None)
        ]

    def delete_deps(self):
        return self.dependencies()


class DataflowDef(ResourceDefinition):
    def __init__(self, resource: dict, override_path):
        self.data_service_id, resource_id, _ = override_path
        super().__init__(resource, 'dataflow', resource_id)

    def dir_path(self, *args, **kwargs):
        return os.path.join(super().dir_path(*args, **kwargs), '__metadata__')

    @property
    def path(self):
        return (self.data_service_id, self.resource_id, None)

    def delete_deps(self):
        result = set()
        for comp_rd in self.rd.get('components', []):
            m = resource_pb2.Resource()
            d = {'component': comp_rd}
            ParseDict(d, m)
            component = ResourceDefinition.from_resource_proto(m, self.path)
            result |= set(component.dependencies())
        return list(result - set([(self.data_service_id, self.resource_id, None)]))

    def contained(self):
        res_defs = []
        for component in self.rd.get('components', []):
            m = resource_pb2.Resource()
            d = {'component': component}
            ParseDict(d, m)
            res_defs.append(ResourceDefinition.from_resource_proto(m, self.path))
        for group in self.rd.get('groups', []):
            m = resource_pb2.Resource()
            d = {'group': group}
            ParseDict(d, m)
            res_defs.append(ResourceDefinition.from_resource_proto(m, self.path))
        return res_defs

    def dependencies(self):
        return [(self.data_service_id, None, None)]

    def make_resource(self, json: dict, rs: 'ResourceSession') -> Resource:
        return model.Dataflow(self.data_service_id, self.resource_id, json, rs.session)


class DataServiceDef(ResourceDefinition):
    def __init__(self, resource: dict, override_path):
        resource_id, _, _ = override_path
        super().__init__(resource, 'dataService', resource_id)

    def dir_path(self, *args, **kwargs):
        return os.path.join(super().dir_path(*args, **kwargs), '__metadata__')

    @property
    def path(self):
        return (self.resource_id, None, None)

    def dependencies(self):
        return []

    def delete_deps(self):
        result = set()
        for df_rd in self.rd.get('dataFeeds', []):
            m = resource_pb2.Resource()
            d = {'dataFeed': df_rd}
            ParseDict(d, m)
            data_feed = ResourceDefinition.from_resource_proto(m, self.path)
            result.add((data_feed.data_service_id, None, None))
        return list(result - set([(self.resource_id, None, None)]))

    def contained(self):
        res_defs = []
        for dataflow in self.rd.get('dataflows', []):
            m = resource_pb2.Resource()
            d = {'dataflow': dataflow}
            ParseDict(d, m)
            res_defs.append(ResourceDefinition.from_resource_proto(m, self.path))
        for data_feed in self.rd.get('dataFeeds', []):
            m = resource_pb2.Resource()
            d = {'dataFeed': data_feed}
            ParseDict(d, m)
            res_defs.append(ResourceDefinition.from_resource_proto(m, self.path))
        return res_defs

    def apply(self, rs: 'ResourceSession') -> Resource:
        res = self.to_resource(rs)
        res.apply()
        rs.refresh_roles()
        return res

    def make_resource(self, json, rs):
        return model.DataService(self.resource_id, json_definition=json, session=rs.session)


def extend_rd(rd_path, child):
    if rd_path[0] is None:
        return (child, None, None)
    elif rd_path[1] is None:
        return (rd_path[0], child, None)
    elif rd_path[2] is None:
        return (rd_path[0], rd_path[1], child)
    else:
        raise ValueError(f"No child possible for {rd_path}")


class ResourcePath:
    def __init__(self, rd_path=None, resource=None):
        self.resource = resource
        if rd_path is None:
            self.rd_path = resource.get_rd_path()
        else:
            self.rd_path = rd_path
        if self.rd_path != ROOT_PATH:
            if resource is None:
                raise ValueError('Only ROOT_PATH may have no resource')
            self.api_path = resource.base_api_path + '/' + resource.resource_id
            if isinstance(resource, model.DataService):
                self.res_type = 'Data Service'
            elif isinstance(resource, model.Dataflow):
                self.res_type = 'Dataflow'
            elif isinstance(resource, Component):
                self.res_type = resource.component_type
            else:
                raise ValueError(f'Invalid resource for path: {resource}')
        self.exportable = resource is not None

    @staticmethod
    def from_arg(path_str, rs: 'ResourceSession'):
        if path_str == '.':
            return ResourcePath(rd_path=ROOT_PATH)
        else:
            rd_pref = path_str.split('.')
            fill = tuple(None for _ in range(3-len(rd_pref)))
            rd_path = (*rd_pref, *fill)
            return ResourcePath.maybe_from_rd_path(rd_path, rs)

    @staticmethod
    def rd_from_arg(path_str):
        if path_str == '.':
            return ROOT_PATH
        else:
            rd_pref = path_str.split('.')
            fill = tuple(None for _ in range(3-len(rd_pref)))
            rd_path = (*rd_pref, *fill)
            return rd_path

    @staticmethod
    def maybe_from_rd_path(rd_path, rs):
        res = rs.get_resource(*rd_path)
        if res.get_rd_path() != rd_path:
            raise ValueError(f'Resource not pathable {res}: {rd_path} vs {res.get_rd_path()}')
        if not res.exportable:
            return None
        return ResourcePath(resource=res)

    def children(self, rs: 'ResourceSession'):
        if self.rd_path == ROOT_PATH:
            def ds_child(child_rd_path):
                return child_rd_path[0] is not None and \
                       child_rd_path[1] is None and \
                       child_rd_path[2] is None
            rs.load_env()
            source = list(filter(ds_child, rs.path_to_uuid.keys()))
        elif isinstance(self.resource, model.DataService):
            def df_child(child_rd_path):
                return child_rd_path[0] == self.rd_path[0] and \
                       child_rd_path[1] is not None and \
                       child_rd_path[2] is None
            rs.load_data_service(self.resource)
            source = list(filter(df_child, rs.path_to_uuid.keys()))
        elif isinstance(self.resource, model.Dataflow):
            def res_child(child_rd_path):
                return child_rd_path[0] == self.rd_path[0] and \
                       child_rd_path[1] is self.rd_path[1] and \
                       child_rd_path[2] is not None
            rs.load_dataflow(self.resource)
            source = list(filter(res_child, rs.path_to_uuid.keys()))
        else:
            source = []
        return filter_none(
            ResourcePath.maybe_from_rd_path(child, rs)
            for child in source
        )

    def dump(self, origin_path: 'ResourcePath', depth):
        if self.rd_path == ROOT_PATH:
            return
        if origin_path.rd_path == self.rd_path:
            suff = '.'.join(filter_none(self.rd_path))
        else:
            strip = len(filter_none(origin_path.rd_path))
            suff = '.'.join(filter_none(self.rd_path[strip:]))
            # need to strip of data matching origin path
        print(depth * "\t" + f'{self.res_type} - {suff}')


class ResourceSession:
    def __init__(self, client, session):
        self.session = session
        self.client = client
        self.path_to_uuid = {}
        self.type_to_api_path_to_uuid = defaultdict(dict)
        self.content_path_to_group_path = {}
        self.group_path_to_content_path = {}
        self.dirty_groups = set()
        self.applied_paths = set()
        self.loaded = set()
        self.uuid_to_resource = {}
        self.roles = None
        self.pub_uuid_to_dfc = {}
        self.list_only = False

    def update_group(self, group_path: Optional, content_path):
        old_group = self.content_path_to_group_path.get(content_path)
        if old_group == group_path:
            return
        if old_group is not None:
            self.dirty_groups.add(old_group)
            self.group_path_to_content_path[old_group].remove(content_path)
        if group_path is None:
            return
        self.dirty_groups.add(group_path)
        self.content_path_to_group_path[content_path] = group_path
        content = self.group_path_to_content_path.get(group_path, set())
        content.add(content_path)
        self.group_path_to_content_path[group_path] = content

    def api_path_to_resource(self, api_path) -> Resource:
        # rd_path: tuple (ds_id, df_id, comp_id) -> illegal for groups
        # api_path: str {ds_id}/{df_id}/{api_type}/resource_id
        if api_path not in self.type_to_api_path_to_uuid:
            raise KeyError(f'path {api_path} not found')
        return self.uuid_to_resource[self.type_to_api_path_to_uuid[api_path]]

    def path_to_def(self, path):
        pass

    def load_defs(self, rd_path, options):
        self.load_defs_recur(options.input, options.input, rd_path, options)

    def load_defs_recur(self, origin, path, rd_path, options):
        p = path
        if os.path.isdir(path):
            p = os.path.join(path, '__metadata__.yaml')
            if not os.path.exists(p):
                if origin == path:
                    raise ValueError(f"Path {p} does not exist!")
                else:
                    # if we are not at the top level, we will skip
                    # directories missing a metadata file
                    return
        _, ext = os.path.splitext(p)
        if ext != '.yaml':
            # only load yaml files
            if origin == path:
                raise ValueError(f"Resource definitions must be yaml files (found {p})")
            return
        ascend_dir, _ = os.path.split(p)
        try:
            with open(p, 'r') as f:
                raw_template = f.read()
            env = jinja.setup_jinja_env(loader=jinja2.FileSystemLoader(ascend_dir))
            data = env.from_string(raw_template).render(config=options.config,
                                                        resourceParentDirectory=ascend_dir)
            res_proto = resource_pb2.Resource()
            d = yaml.load(data, Loader=yaml.SafeLoader)
            ParseDict(d, res_proto)
        except Exception as e:
            raise Exception(f"Unable to load resource definition from {p}") from e
        res_def = ResourceDefinition.from_resource_proto(res_proto, rd_path)
        self.path_to_def[res_def.path] = res_def
        if options.recursive:
            self.load_contained_defs(res_def)
            if os.path.isdir(path):
                child_paths = os.listdir(path)
                for child_path in child_paths:
                    if child_path == '__metadata__.yaml':
                        continue
                    name, _ = os.path.splitext(child_path)
                    self.load_defs_recur(origin, os.path.join(path, child_path),
                                         extend_rd(rd_path, name), options)

    def load_contained_defs(self, res_def):
        contained = res_def.contained()
        if len(contained) > 0:
            for c in contained:
                self.path_to_def[c.path] = c
                self.load_contained_defs(c)

    def apply(self, res_path_str, creds, options):
        # load resource defs from directory: path_to_def
        self.path_to_def = {}
        # need to handle case where there is no resource in api for path
        rd_path = ResourcePath.rd_from_arg(res_path_str)
        self.load_defs(rd_path, options)
        marked_paths = {rd_path}
        g = nx.DiGraph()
        for path, res_def in self.path_to_def.items():
            marked_paths.add(path)
            g.add_node(path)
            for dep in res_def.dependencies():
                g.add_edge(path, dep)
            for dep in res_def.dependees():
                g.add_edge(dep, path)

        groups = set()
        for path in g.nodes:
            if path not in self.path_to_def:
                # just load info from api to supply a dependency, do not need to apply
                try:
                    self.get_resource(*path)
                except Exception as e:
                    raise KeyError(f'Unable to load dependency {path}') from e

        for path in reversed(list(nx.topological_sort(g))):
            if path not in self.path_to_def:
                continue
            else:
                res_def = self.path_to_def[path]
                if isinstance(res_def, GroupDef):
                    # groups need to go last
                    groups.add(res_def)
                    continue
                for transform in res_def.transforms:
                    transform.to_api(creds=creds)
                sh.info(f'APPLY: {res_def.path}')
                sh.debug(res_def.resource)
                if not options.dry_run:
                    res = res_def.apply(self)
                    self.path_to_uuid[path] = res.uuid
                    self.uuid_to_resource[res.uuid] = res
                else:
                    try:
                        res = self.get_resource(*res_def.path)
                        self.path_to_uuid[path] = res.uuid
                        self.uuid_to_resource[res.uuid] = res
                    except KeyError:
                        sh.info(f'Unable to get {res_def.path} during dry run')

        group_paths = self.dirty_groups | {g.path for g in groups}
        for group_path in group_paths:
            group_def = self.path_to_def.get(group_path)
            if group_def is None:
                # Not creating, must already exist
                group_uuid = self.get_resource(*group_path).uuid
                if group_uuid is None:
                    raise KeyError(f'Unable to find group {group_path}')
                group_res = self.uuid_to_resource[group_uuid]
                group_def = ResourceDefinition.from_resource_proto(
                    group_res.to_resource_proto(self, options),
                    (group_res.data_service_id, group_res.dataflow_id, group_res.resource_id))

            sh.info(f'APPLY: {group_def.path}')
            if not options.dry_run:
                group_def.apply(self)

        if options.delete and options.recursive:
            for child in ResourcePath.from_arg(res_path_str, self).children(self):
                if child.exportable and child.rd_path not in marked_paths:
                    self._delete(child, options)

    def list(self, path_str, recursive):
        self.list_only = True
        res_path = ResourcePath.from_arg(path_str, self)
        return self._list(res_path, res_path, recursive, 0 - (res_path != ROOT_PATH))

    def _list(self, origin, res_path: ResourcePath, recursive, depth):
        if not res_path.exportable:
            return
        res_path.dump(origin, depth)
        if origin.rd_path == res_path.rd_path or recursive:
            for child_path in res_path.children(self):
                self._list(origin, child_path, recursive, depth+1)

    def get(self, path_str, options):
        res_path = ResourcePath.from_arg(path_str, self)
        if not res_path:
            raise ValueError(f'{path_str} is not exportable!')
        if res_path.rd_path[0] is None:
            raise ValueError('Cannot get root path!')
        sh.debug(f'origin: {res_path}')
        creds_snippet = {}
        self._get(res_path, res_path, options, creds_snippet)
        if options.output is not None:
            sys.stdout.write(ascend.credentials.dump_credentials(creds_snippet))

    def _get(self, origin, res_path: ResourcePath, options, creds_snippet):
        # load resources for path
        if options.recursive:
            for child_path in res_path.children(self):
                self._get(origin, child_path, options, creds_snippet)
        if res_path.exportable:
            proto = res_path.resource.to_resource_proto(self, options)
            res_def = ResourceDefinition.from_resource_proto(proto, res_path.rd_path)
            for transform in res_def.all_transforms():
                if isinstance(transform, transforms.Creds):
                    creds_snippet.update(transform.snippet())
            if options.directory:
                assert options.output is not None, "output req'd for dir"
                res_def.dump(origin, options)
            else:
                # have integrated to root, time to dump
                if origin == res_path:
                    res_def.dump(origin, options)

    def delete(self, res_path_str, options):
        res_path = ResourcePath.from_arg(res_path_str, self)
        if not res_path:
            raise ValueError(f'{res_path_str} is not deletable!')
        if res_path.rd_path[0] is None:
            raise ValueError('Cannot delete root path!')
        self._delete(res_path, options)

    def _delete(self, res_path, options):
        children = res_path.children(self)
        if len(children) > 0 and not options.recursive:
            raise ValueError(f'Cannot delete {res_path.rd_path} without '
                             f'recursive flag, contains children')
        if isinstance(res_path.resource, model.Dataflow):
            self.load_dataflow(res_path.resource)
            df_uuids = [
                v for k, v in self.type_to_api_path_to_uuid['pub'].items()
                if k[0] == res_path.resource.data_service_id
                   and k[1] == res_path.resource.dataflow_id
            ]
            if len(df_uuids) > 0:
                dfs = list(map(self.uuid_to_resource.get, df_uuids))
                raise ValueError(f'Cannot delete dataflow which contains data feeds: {dfs}')
        sh.info(f'DELETE {res_path.rd_path}')
        if not options.dry_run:
            res_path.resource.delete()

    def load_env(self):
        if ROOT_PATH not in self.loaded:
            dss = self.client.list_data_services()
            for ds in dss:
                self.uuid_to_resource[ds.uuid] = ds
                self.path_to_uuid[ds.get_rd_path()] = ds.uuid
                self.type_to_api_path_to_uuid['organization'][ds.get_api_path()] = ds.uuid
            if not self.list_only:
                self.refresh_roles()
            self.loaded.add(ROOT_PATH)

    def refresh_roles(self):
        roles = self.client.list_roles()
        self.roles = roles
        for role in roles:
            self.uuid_to_resource[role['uuid']] = role

    def load_data_service(self, ds):
        path = ds.get_api_path()
        if path not in self.loaded:
            dfs = ds.list_dataflows()
            # cannot use list_data_feeds because we won't get the full json
            for df in dfs:
                try:
                    self.uuid_to_resource[df.uuid] = df
                    self.path_to_uuid[df.get_rd_path()] = df.uuid
                    self.type_to_api_path_to_uuid[df.api_type][df.get_api_path()] = df.uuid
                except Exception as e:
                    raise ValueError(f'Unable to extract from {df}') from e
                if not self.list_only:
                    self.load_dataflow(df)
            self.loaded.add(path)

    def load_dataflow(self, dataflow):
        path = dataflow.get_api_path()
        if path not in self.loaded:
            resources = dataflow.list_components()
            if not self.list_only:
                groups = dataflow.list_groups()
                resources.extend(groups)
            for res in resources:
                if isinstance(res, model.ReadConnector) and not self.list_only:
                    # Direct load for blob sources
                    cont = res.json_definition['source'].get('container', {})
                    if cont.get('immediate') is not None:
                        payload = self.session.get(res.resource_path)['data']
                        res = model.ReadConnector(res.data_service_id, res.dataflow_id,
                                                  res.component_id, payload, res.session)
                elif isinstance(res, model.DataFeedConnector):
                    self.pub_uuid_to_dfc[res.json_definition['pubUUID']] = res
                self.uuid_to_resource[res.uuid] = res
                self.type_to_api_path_to_uuid[res.api_type][res.get_api_path()] = res.uuid
                try:
                    k = res.get_rd_path()
                    self.path_to_uuid[k] = res.uuid
                except NotImplementedError:
                    # groups and subs do not have rd paths
                    continue
            if not self.list_only:
                for group in groups:
                    for item in group.json_definition['content']:
                        res = self.uuid_to_resource[item['uuid']]
                        try:
                            res_path = res.get_rd_path()
                            group_path = group.get_api_path()
                            self.content_path_to_group_path[res_path] = group_path
                            prev_cont = self.group_path_to_content_path.get(group_path, set())
                            self.group_path_to_content_path[group_path] = prev_cont | {res_path}
                        except NotImplementedError:
                            # subs do not have rd paths
                            continue
            self.loaded.add(path)

    def get_ds(self, data_service_id) -> 'model.DataService':
        k = (data_service_id, None, None)
        if k not in self.path_to_uuid:
            ds = self.client.get_data_service(data_service_id)
            self.uuid_to_resource[ds.uuid] = ds
            self.path_to_uuid[ds.get_rd_path()] = ds.uuid
            self.type_to_api_path_to_uuid[ds.get_api_path()] = ds.uuid
        return self.uuid_to_resource[self.path_to_uuid[k]]

    def get_df(self, data_service_id, df_id):
        keygen = lambda _df_id: (data_service_id, _df_id, None)
        k = keygen(df_id)
        if k not in self.path_to_uuid:
            ds = self.get_ds(data_service_id)
            self.load_data_service(ds)
        return self.uuid_to_resource[self.path_to_uuid[k]]

    def get_resource(self, data_service_id, df_id: Optional[str],
                     resource_id: Optional[str]) -> Resource:
        if data_service_id is None:
            raise ValueError("Must provide data_service_id")
        elif df_id is None:
            return self.get_ds(data_service_id)
        elif resource_id is None:
            return self.get_df(data_service_id, df_id)
        keygen = lambda rid: (data_service_id, df_id, rid)
        k = keygen(resource_id)
        if k not in self.path_to_uuid:
            dataflow = self.get_df(data_service_id, df_id)
            self.load_dataflow(dataflow)
        return self.uuid_to_resource[self.path_to_uuid[k]]


def resolve_path(arg_path, base_path, res_path) -> str:
    '''
    e.g.
    arg = new_resource
    base_path = ('ds_id', 'df_id', None)
    res_path = ('ds_id', 'df_id', 'comp_id')
    returns: new_resource/comp_id
    :param path string
    :param base resource path
    :param target resource path
    :return:
    '''
    assert len(filter_none(base_path)) <= len(filter_none(res_path))
    if base_path == res_path:
        return arg_path
    strip_length = len(filter_none(base_path))
    sh.debug(res_path)
    overrides = '/'.join(filter_none(res_path[strip_length:]))
    return os.path.join(arg_path, overrides)


def coalesce(*l):
    return next(filter(lambda e: e is not None, l), None)
