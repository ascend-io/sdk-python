from ascend import util
from ascend.resource import Component, Resource
from google.protobuf.json_format import MessageToDict, Parse, ParseDict
from ascend.protos.resource import resource_pb2
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from ascend.resource_definitions import ResourceSession

import json

RENAME_MAP = {
    'sub': 'data_feed_connector',
    'pub': 'data_feed',
    'source': 'read_connector',
    'view': 'transform',
    'sink': 'write_connector',
    'project': 'dataflow',
    'organization': 'data_service',
}

class DataService(Resource):
    """
    A Data Service is the highest-level organizational structure in
    Ascend, and the primary means of controlling access.
    It contains one or more Dataflows and can communicate with other
    Data Services via Data Feeds.

    # Parameters
    data_service_id (str):
        The ID of the Data Service to connect to
    json_definition (dict):
        The API's JSON definition of the Data Service.
        Used, if provided, to construct the DataService directly
        and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """

    def __init__(self, data_service_id, json_definition=None, session=None):
        super().__init__(data_service_id, "organizations", json_definition=json_definition, session=session)

        # Override raw_json fields
        self.json_definition["id"] = self.resource_id
        self.json_definition["name"] = self.resource_id.replace("_", " ")
        self.data_service_id = data_service_id
        self.api_type = 'organization'
        self.resource_type = 'data_service'

    def get_rd_path(self):
        return (self.resource_id, None, None)

    def get_dataflow(self, dataflow_id, raw=False):
        """
        Get a Dataflow from within the Data Service

        # Parameters
        dataflow_id (str): the ID of the Dataflow

        # Returns
        Dataflow: the Dataflow

        # Raises
        HTTPError: on API errors
        """
        raw_resp = self.session.get("{}/projects/{}".format(self.resource_path, dataflow_id))
        if raw:
            return raw_resp

        return Dataflow(self.resource_id, dataflow_id, json_definition=raw_resp, session=self.session)

    def list_dataflows(self, raw=False) -> List['Dataflow']:
        """
        List all the Dataflows in the Data Service which are accessible to the Client.

        # Returns
        List<Dataflow>: the Dataflows

        # Raises
        HTTPError: on API errors
        """
        raw_resp = self.session.get("{}/projects".format(self.resource_path))
        if raw:
            return raw_resp

        return list(map(
            lambda df:
            Dataflow(self.resource_id, df['id'], json_definition=df, session=self.session),
            raw_resp['data']
        ))

    def rd_path(self):
        return (self.data_service_id, None, None)

    def to_type_proto(self, rs: 'ResourceSession', options, top_level=False):
        d = {}
        if top_level:
            self.set_boilerplate(d)
        rs.load_data_service(self)
        pub_uuids = [
            v for k, v in rs.type_to_api_path_to_uuid['pub'].items()
            if k[0] == self.data_service_id
        ]
        d['dataFeeds'] = sorted([
            MessageToDict(rs.uuid_to_resource[uuid].to_type_proto(rs, options, top_level=True))
            for uuid in pub_uuids
        ], key=lambda d: d['id'])
        if options.recursive and not getattr(options, 'directory', False):
            uuids = [
                v for k, v in rs.type_to_api_path_to_uuid['project'].items()
                if k[0] == self.data_service_id
            ]
            d['dataflows'] = sorted([
                MessageToDict(rs.uuid_to_resource[uuid].to_type_proto(rs, options, top_level=True))
                for uuid in uuids
            ], key=lambda d: d['id'])
        message = resource_pb2.DataService()
        Parse(json.dumps(d), message, ignore_unknown_fields=True)
        return message

    def __repr__(self):
        return '<{1}.{2} {0}>'.format(
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__)

class Dataflow(Resource):
    """
        A Dataflow is where Connectors and Transforms are defined,
        and the dependency graph specified.

        # Parameters
        data_service_id (str):
            The ID of the Data Service which contains this Dataflow
        dataflow_id (str):
            The ID of the Dataflow. Must be unique within the Data Service.
        json_definition (dict):
            The API's JSON definition of the Data Service.
            Used, if provided, to construct the DataService directly
            and avoid one API request.
            (default is `None`)
        session (ascend.session.Session):
            The client session used for HTTP requests.

        # Raises
        HTTPError: on API errors
    """

    def __init__(self, data_service_id, dataflow_id, json_definition=None, session=None):
        super().__init__(
            dataflow_id,
            "organizations/{}/projects".format(data_service_id),
            json_definition=json_definition,
            session=session)

        # Parental id's
        self.data_service_id = data_service_id
        self.dataflow_id = dataflow_id
        self.api_type = 'project'

        # Override raw_json id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["dataflow_id"] = self.dataflow_id
        self.json_definition["id"] = self.resource_id
        self.resource_type = 'dataflow'

    def list_components(self) -> List[Component]:
        """
        List the Components (Connectors and Transforms) in the Dataflow.

        # Returns
        List<Component>: the Components

        # Raises
        HTTPError: on API errors
        """
        raw_resp = self.session.get("{}/components?deep=true".format(self.resource_path))

        if not raw_resp['data']:
            return []

        dataflow_components = {}
        for c in raw_resp['data']:
            component = component_definition_to_component(
                self.data_service_id,
                self.resource_id,
                c['id'],
                c,
                self.session)
            if component:
                dataflow_components[component.uuid] = component

        return list(dataflow_components.values())

    def list_groups(self) -> List['Group']:
        """
        List the Groups in the Dataflow.

        # Returns
        List<Groups>: the Groups

        # Raises
        HTTPError: on API errors
        """
        raw_resp = self.session.get("{}/groups".format(self.resource_path))

        if not raw_resp['data']:
            return []

        groups = []
        for c in raw_resp['data']:
            group = Group(self.data_service_id, self.resource_id, c['id'], c, self.session)
            if group:
                groups.append(group)

        return groups

    def get_component(self, component_id):
        """
        Get a Component from a Dataflow

        # Parameters
        component_id (str): the ID of the Component

        # Returns
        Component: the Component

        # Raises
        HTTPError: on API errors
        """
        return list(filter(lambda c: c.resource_id == component_id, self.list_components()))[0]

    def to_type_proto(self, rs: 'ResourceSession', options, top_level=False):
        d = {}
        if top_level:
            self.set_boilerplate(d)
        rs.load_dataflow(self)
        group_uuids = [
            v for k, v in rs.type_to_api_path_to_uuid['group'].items()
            if k[0] == self.data_service_id and k[1] == self.resource_id
        ]
        if options.recursive:
            groups = [rs.uuid_to_resource[uuid] for uuid in group_uuids]
            d['groups'] = sorted([
                MessageToDict(group.to_type_proto(rs, options, top_level=True)) for group in groups
            ], key=lambda d: d['id'])
        if not getattr(options, 'directory', False) and options.recursive:
            # add components for nested style
            uuids = [
                v for t in ['source', 'view', 'sink']
                for k, v in rs.type_to_api_path_to_uuid[t].items()
                if k[0] == self.data_service_id and k[1] == self.dataflow_id
            ]
            protos = [rs.uuid_to_resource[uuid].to_type_proto(rs, options, True) for uuid in uuids]
            d['components'] = sorted([
                MessageToDict(proto) for proto in protos
            ], key=lambda d: d['id'])
        message = resource_pb2.Dataflow()
        ParseDict(d, message)
        return message

    def get_rd_path(self):
        return self.data_service_id, self.dataflow_id, None

    def __repr__(self):
        return '<{2}.{3} {0}.{1}>'.format(
            self.data_service_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__)


class Group(Resource):
    def __init__(self, data_service_id, dataflow_id, group_id, json_definition=None, session=None):
        super().__init__(
            group_id,
            "organizations/{}/projects/{}/groups".format(data_service_id, dataflow_id),
            json_definition=json_definition,
            session=session)

        # Parental id's
        self.data_service_id = data_service_id
        self.dataflow_id = dataflow_id
        self.api_type = 'group'
        self.resource_type = 'group'
        self.exportable = False

        # Override raw_json id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["id"] = self.resource_id

    def to_type_proto(self, rs: 'ResourceSession', options, top_level=False):
        d = {}
        if top_level:
            self.set_boilerplate(d)
        self.set_boilerplate(d)
        message = resource_pb2.Group()
        Parse(json.dumps(d), message, ignore_unknown_fields=True)
        return message

    def get_api_path(self):
        return self.data_service_id, self.dataflow_id, self.resource_id

    def get_rd_path(self):
        return self.data_service_id, self.dataflow_id, self.resource_id

    def __repr__(self):
        return '<{3}.{4} {0}.{1}.{2}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__)


class DataFeed(Component):
    """
    A Data Feed is a live-updated dataset which is produced by a Dataflow in one
    Data Service and can be shared with other Data Services.

    # Parameters
    data_service_id (str):
        The ID of the Data Service producing the Data Feed
    data_feed_id (str):
        The ID of the Data Feed. Must be unique within the Data Service.
    json_definition (dict):
        The API's JSON definition of the Data Feed.
        Used, if provided, to construct the Data Feed directly
        and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """

    def __init__(self, data_service_id, dataflow_id, data_feed_id, json_definition=None, session=None):
        super().__init__(
            data_service_id,
            dataflow_id,
            'pub',
            data_feed_id,
            json_definition=json_definition,
            session=session)
        self.component_type = "DataFeed"
        self.data_feed_id = data_feed_id
        self.resource_type = 'data_feed'
        self.exportable = False

        # Override id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["dataflow_id"] = self.dataflow_id
        self.json_definition["id"] = self.resource_id

    def get_rd_path(self):
        return (self.data_service_id, self.resource_id, None)

    def resource_ref(self, rs: 'ResourceSession'):
        return '.'.join(filter(lambda x: x is not None, self.get_rd_path()))

    def input_uuids(self):
        return [self.json_definition['inputUUID']]

    def to_type_proto(self, rs: 'ResourceSession', options, top_level=False):
        d = {}
        if top_level:
            self.set_boilerplate(d)
        rd_path = self.get_rd_path()
        if rd_path in rs.content_path_to_group_path:
            d['group_id'] = rs.content_path_to_group_path[rd_path][2]
        self.set_details(rs, d, options)
        message = resource_pb2.DataFeed()
        ParseDict(d, message)
        return message

    def set_details(self, rs, d, options):
        dataflow = rs.get_resource(self.data_service_id, self.dataflow_id, None)
        rs.load_dataflow(dataflow)
        inp = rs.uuid_to_resource[self.json_definition['inputUUID']]
        if self.json_definition['open']:
            sharing = {'all': True}
        else:
            shared_ds = set()
            rs.load_env()
            hidden = True  # hidden means data feed is not shared with its own data service
            for roleUUID in self.json_definition['pubToRoles'].split(','):
                role = rs.uuid_to_resource.get(roleUUID)
                if not role:
                    # org-specific roles can be ignored
                    continue
                if role['id'] == 'Everyone':
                    ds = rs.uuid_to_resource[role['orgId']]
                    if ds.resource_id == self.data_service_id:
                        hidden = False
                    else:
                        shared_ds.add(ds.resource_id)
            sharing = {'data_services': list(shared_ds)}
            # print(self.json_definition)
            if hidden:
                sharing = {**sharing, 'hidden': True}
        d['input_id'] = f'{inp.dataflow_id}.{inp.resource_id}'
        d['sharing'] = sharing

    def get_api_path(self):
        return super().get_rd_path()

    def __repr__(self):
        return '<{2}.{3} {0}.{1}>'.format(
            self.data_service_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__)


class DataFeedConnector(Component):
    def __init__(self, data_service_id, dataflow_id, data_feed_connector_id, json_definition=None, session=None):
        super().__init__(
            data_service_id,
            dataflow_id,
            'sub',
            data_feed_connector_id,
            json_definition=json_definition,
            session=session)
        self.component_type = "DataFeedConnector"
        self.json_definition = json_definition

        # Override id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["dataflow_id"] = self.dataflow_id
        self.json_definition["id"] = self.resource_id
        self.exportable = False

    def set_details(self, *args):
        raise NotImplementedError(f'{self} does not have an rd representation')

    def get_rd_path(self):
        raise NotImplementedError(f'{self} does not have an rd representation')

    def input_uuids(self) -> List[str]:
        return [self.json_definition['pubUUID']]

    # data feed connectors need to supply a reference to their pub
    def resource_ref(self, rs: 'ResourceSession'):
        pubUUID = self.json_definition['pubUUID']
        if pubUUID not in rs.uuid_to_resource:
            payload = self.session.get(f'{self.base_api_path}/{self.resource_id}/pub')['data']
            # workaround for this call sometimes returning public-only data
            pub_data_service_id = payload.get('orgId') or payload['organization']['id']
            pub_dataflow_id = payload.get('prjId') or payload['project']['id']
            origin_dataflow = rs.get_df(pub_data_service_id, pub_dataflow_id)
            # just load the whole dataflow
            rs.load_dataflow(origin_dataflow)
        return rs.uuid_to_resource[pubUUID].resource_ref(rs)

    def get_api_path(self):
        return super().get_rd_path()

    def __repr__(self):
        return '<{3}.{4} {0}.{1}.{2} type={5}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__,
            self.component_type)


class ReadConnector(Component):
    """
    Components are the functional units in a Dataflow.
    There are two main types of Components: Connectors and Transforms.

    # Parameters
    data_service_id (str):
        The ID of the Data Service which contains this Dataflow
    dataflow_id (str):
        The ID of the Dataflow. Must be unique within the Data Service.
    component_id (str):
        The ID of the Component. Must be unique within the Dataflow.
    json_definition (dict):
        The API's JSON definition of the Data Service.
        Used, if provided, to construct the DataService directly and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """

    def __init__(self, data_service_id, dataflow_id, component_id, json_definition=None, session=None):
        super().__init__(
            data_service_id,
            dataflow_id,
            'source',
            component_id,
            json_definition=json_definition,
            session=session)
        self.component_type = "ReadConnector"

        # Override id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["dataflow_id"] = self.dataflow_id
        self.json_definition["id"] = self.resource_id

    def refresh(self):
        """
        Triggers a refresh on Read Connectors.

        # Raises
        HttpError: on API errors
        """
        self.session.post(self.resource_api_path + "/refresh")

    def set_details(self, rs: 'ResourceSession', d, options):
        d['read_connector'] = self.json_definition['source']

    def __repr__(self):
        return '<{3}.{4} {0}.{1}.{2} type={5}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__,
            self.component_type)


class Transform(Component):
    """
    Components are the functional units in a Dataflow.
    There are two main types of Components: Connectors and Transforms.

    # Parameters
    data_service_id (str):
        The ID of the Data Service which contains this Dataflow
    dataflow_id (str):
        The ID of the Dataflow. Must be unique within the Data Service.
    component_id (str):
        The ID of the Component. Must be unique within the Dataflow.
    json_definition (dict):
        The API's JSON definition of the Data Service.
        Used, if provided, to construct the DataService directly and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """

    def __init__(self, data_service_id, dataflow_id, component_id, json_definition=None, session=None):
        super().__init__(
            data_service_id,
            dataflow_id,
            'view',
            component_id,
            json_definition=json_definition,
            session=session)
        self.component_type = "Transform"

        # Override id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["dataflow_id"] = self.dataflow_id
        self.json_definition["id"] = self.resource_id

    def set_details(self, rs: 'ResourceSession', d, options):
        input_ress = map(rs.uuid_to_resource.get, self.input_uuids())
        d['transform'] = {
            **self.json_definition['view'],
            'input_ids': [input_res.resource_ref(rs) for input_res in input_ress]
        }

    def input_uuids(self) -> List[str]:
        return [input['uuid'] for input in self.json_definition['inputs']]

    @classmethod
    def apply_rename(cls, json_definition):
        name_mapping = {"view": "transform"}
        for old_name, new_name in name_mapping.items():
            if old_name in json_definition:
                json_definition[new_name] = json_definition[old_name]
                del json_definition[old_name]
        return json_definition

    def __repr__(self):
        return '<{3}.{4} {0}.{1}.{2} type={5}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__,
            self.component_type)


class WriteConnector(Component):
    """
    Components are the functional units in a Dataflow.
    There are two main types of Components: Connectors and Transforms.

    # Parameters
    data_service_id (str):
        The ID of the Data Service which contains this Dataflow
    dataflow_id (str):
        The ID of the Dataflow. Must be unique within the Data Service.
    component_id (str):
        The ID of the Component. Must be unique within the Dataflow.
    json_definition (dict):
        The API's JSON definition of the Data Service.
        Used, if provided, to construct the DataService directly and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """

    def __init__(self, data_service_id, dataflow_id, component_id, json_definition=None, session=None):
        super().__init__(
            data_service_id,
            dataflow_id,
            'sink',
            component_id,
            json_definition=json_definition,
            session=session)
        self.component_type = "WriteConnector"

        # Override id's
        self.json_definition["data_service_id"] = self.data_service_id
        self.json_definition["dataflow_id"] = self.dataflow_id
        self.json_definition["id"] = self.resource_id

    def input_uuids(self) -> List[str]:
        return [self.json_definition['inputUUID']]

    def set_details(self, rs: 'ResourceSession', d, options):
        input_uuid = self.json_definition['inputUUID']
        input_res = rs.uuid_to_resource[input_uuid]
        d['write_connector'] = {
            **self.json_definition['sink'],
            'input_id': input_res.resource_id
        }

    def __repr__(self):
        return '<{3}.{4} {0}.{1}.{2} type={5}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.resource_id,
            self.__class__.__module__,
            self.__class__.__qualname__,
            self.component_type)


def component_from_json(json_definition, session):
    data_service_id = json_definition['organization']['id']
    dataflow_id = json_definition['project']['id']
    component_id = json_definition['id']
    return component_definition_to_component(
        data_service_id,
        dataflow_id,
        component_id,
        json_definition,
        session
    )


def component_definition_to_component(data_service_id, dataflow_id, component_id, c, session):
    component_type = util.parse_component_type(c)

    if component_type == "ReadConnector":
        return ReadConnector(data_service_id, dataflow_id, component_id, json_definition=c, session=session)
    elif component_type == "Transform":
        return Transform(data_service_id, dataflow_id, component_id, json_definition=c, session=session)
    elif component_type == "WriteConnector":
        return WriteConnector(data_service_id, dataflow_id, component_id, json_definition=c, session=session)
    elif component_type == "DataFeed":
        return DataFeed(data_service_id, dataflow_id, component_id, json_definition=c, session=session)
    elif component_type == "DataFeedConnector":
        return DataFeedConnector(data_service_id, dataflow_id, component_id, json_definition=c, session=session)
