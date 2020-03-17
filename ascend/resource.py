from requests import HTTPError
import ascend.cli.global_values as global_values
from google.protobuf.message import Message
from google.protobuf.json_format import ParseDict
from ascend.protos.resource import resource_pb2
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from ascend.resource_definitions import ResourceSession


class Resource:
    def __init__(self, resource_id, api_path, json_definition=None, session=None):
        if not session:
            raise ValueError("Must have a valid session for this resource.")

        self.resource_id = resource_id
        self.base_api_path = api_path
        self.resource_path = f'{api_path}/{resource_id}'
        self.session = session

        if not json_definition:
            try:
                json_definition = self.session.get(f"{api_path}/{resource_id}")
            except KeyError as e:
                raise KeyError(f"{resource_id} not found") from e
            if 'data' in json_definition:
                json_definition = json_definition['data']
        self.json_definition = json_definition
        self.uuid = self.json_definition.get('uuid')
        self.exportable = True

    # we can have these fields located at different levels of the proto message
    def set_boilerplate(self, d):
        d['id'] = self.resource_id
        d['name'] = self.json_definition['name']
        d['description'] = self.json_definition.get('description', '')

    def to_resource_proto(self, rs: 'ResourceSession', options) -> 'resource_pb2.Resource':
        d = {
            'version': global_values.API_VERSION,
        }
        self.set_boilerplate(d)
        type_message = self.to_type_proto(rs, options)
        message = resource_pb2.Resource(**{**d, **{self.resource_type: type_message}})
        return message

    def to_type_proto(self, rs: 'ResourceSession', options, top_level=False) -> Message:
        raise NotImplementedError(self)

    def get_rd_path(self):
        raise NotImplementedError(self)

    def apply(self):
        """
        Upserts this Resource

        # Raises
        HTTPError: on API errors
        """
        exists = False
        try:
            self.session.get(self.resource_path)
            exists = True
        except KeyError:
            pass
        except HTTPError as e:
            if e.response and e.response.status_code == 404:
                pass
            else:
                raise e
        try:
            if exists:
                self.session.patch(self.resource_path, data=self.json_definition)
            else:
                self.session.post(self.base_api_path, data=self.json_definition)
            self.json_definition = self.session.get(self.resource_path)['data']
            self.uuid = self.json_definition['uuid']
        except HTTPError as e:
            details = f'unable to apply {self.resource_path}'
            if e.response is not None:
                details = f'{details}: {e.response.content}'
            raise Exception(details) from e

    def delete(self):
        """
        Deletes this Resource

        # Raises
        HTTPError: on API errors
        """
        try:
            self.session.delete(self.resource_path)
        except HTTPError as e:
            details = f'unable to delete {self.resource_path}'
            if e.response is not None:
                details = f'{details}: {e.response.content}'
            raise Exception(details) from e

    def get_api_path(self):
        return self.get_rd_path()


class Component(Resource):
    def __init__(self,
                 data_service_id,
                 dataflow_id,
                 api_type,
                 component_id,
                 json_definition=None,
                 session=None):
        api_path = 'organizations/{}/projects/{}/{}s'.format(
            data_service_id,
            dataflow_id,
            api_type
        )
        super().__init__(component_id, api_path, json_definition, session)
        self.data_service_id = data_service_id
        self.dataflow_id = dataflow_id
        self.api_type = api_type
        self.component_id = component_id
        self.resource_type = "component"

    def input_uuids(self) -> List[str]:
        return []

    def get_rd_path(self):
        return (self.data_service_id, self.dataflow_id, self.resource_id)

    def resource_ref(self, rs: 'ResourceSession'):
        return self.component_id

    def set_details(self, rs: 'ResourceSesion', d, options):
        raise NotImplementedError(self)

    def to_type_proto(self, rs: 'ResourceSession', options, top_level=False):
        d = {}
        if top_level:
            self.set_boilerplate(d)
        rd_path = self.get_rd_path()
        if rd_path in rs.content_path_to_group_path:
            d['group_id'] = rs.content_path_to_group_path[rd_path][2]
        self.set_details(rs, d, options)
        message = resource_pb2.Component()
        ParseDict(d, message, ignore_unknown_fields=True)
        return message

    def get_records(self, offset=0, limit=0):
        """
        Get the records of data from the Data Feed.

        # Parameters
        offset (int):
            index at which records will start streaming from
        limit (int):
            maximum number of records that should be returned

        # Returns
        Iterator<dict>:
            An iterator over the records of data.
            Can be read into a Pandas DataFrame using `Pandas.DataFrame.from_records()`.

        # Raises
        ValueError: on invalid query parameter inputs
        HTTPError:  on API errors
        """
        if offset < 0:
            raise ValueError("Offset must be a non-negative value.")
        if limit < 0:
            raise ValueError("Limit must be a non-negative value.")
        query_params = {}
        if offset > 0:
            query_params["offset"] = offset
        if limit > 0:
            query_params["limit"] = limit

        return self.session.stream(self.resource_path + "/records-stream", query=query_params)


