"""
Ascend Model module

The Model module provides client-side representations of resources in
Ascend, including Data Services, Dataflows, Data Feeds, and Components.
"""

from ascend.util import parse_component_type, type_displayname
from urllib.error import HTTPError


class DataService:
    """
    A Data Service is the highest-level organizational structure in
    Ascend, and the primary means of controlling access.
    It contains one or more Dataflows and can communicate with other
    Data Services via Data Feeds.

    # Parameters
    data_service_id (str):
        The ID of the Data Service to connect to
    raw_json (dict):
        The API's JSON definition of the Data Service.
        Used, if provided, to construct the DataService directly
        and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """
    def __init__(self, data_service_id, raw_json=None, session=None):
        self.data_service_id = data_service_id
        self.session = session
        self.prefix = "organizations/{}".format(self.data_service_id)

        if raw_json is None and session is not None:
            raw_json = self.session.get(self.prefix) # to confirm access

    def list_dataflows(self, raw=False):
        """
        List all the Dataflows in the Data Service which are accessible to the Client.

        # Returns
        List<Dataflow>: the Dataflows

        # Raises
        HTTPError: on API errors
        """
        raw_resp = self.session.get("{}/projects".format(self.prefix))
        if raw:
            return raw_resp

        return list(map(
            lambda df:
                Dataflow(self.data_service_id, df['id'], raw_json=df, session=self.session),
            raw_resp['data']
        ))

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
        raw_resp = self.session.get("{}/projects/{}".format(self.prefix, dataflow_id))
        if raw:
            return raw_resp

        return Dataflow(self.data_service_id, dataflow_id, raw_json=raw_resp, session=self.session)

    def __repr__(self):
        return '<{1}.{2} {0}>'.format(
            self.data_service_id,
            self.__class__.__module__,
            self.__class__.__qualname__)


class DataFeed:
    """
    A Data Feed is a live-updated dataset which is produced by a Dataflow in one
    Data Service and can be shared with other Data Services.

    # Parameters
    data_service_id (str):
        The ID of the Data Service producing the Data Feed
    data_feed_id (str):
        The ID of the Data Feed. Must be unique within the Data Service.
    raw_json (dict):
        The API's JSON definition of the Data Feed.
        Used, if provided, to construct the Data Feed directly
        and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """
    def __init__(self, data_service_id, data_feed_id, raw_json = None, session = None):
        self.data_service_id = data_service_id
        self.data_feed_id = data_feed_id
        self.session = session

        if raw_json is None:
            # ATM we must have the JSON for the data feed to construct the prefix
            raise ValueError("must provide JSON to construct DataFeed")

        self.prefix =  "organizations/{}/projects/{}/pubs/{}".format(
            data_service_id, raw_json['fromProjUUID'], raw_json['uuid'])

    def get_records(self):
        """
        Get the records of data from the Data Feed.

        # Returns
        Iterator<dict>:
            An iterator over the records of data.
            Can be read into a Pandas DataFrame using `Pandas.DataFrame.from_records()`.

        # Raises
        HTTPError: on API errors
        """
        return self.session.stream(self.prefix + "/records-stream")

    def __repr__(self):
        return '<{2}.{3} {0}.{1}>'.format(
            self.data_service_id,
            self.data_feed_id,
            self.__class__.__module__,
            self.__class__.__qualname__)


class Dataflow:
    """
        A Dataflow is where Connectors and Transforms are defined,
        and the dependency graph specified.

        # Parameters
        data_service_id (str):
            The ID of the Data Service which contains this Dataflow
        dataflow_id (str):
            The ID of the Dataflow. Must be unique within the Data Service.
        raw_json (dict):
            The API's JSON definition of the Data Service.
            Used, if provided, to construct the DataService directly
            and avoid one API request.
            (default is `None`)
        session (ascend.session.Session):
            The client session used for HTTP requests.

        # Raises
        HTTPError: on API errors
    """
    def __init__(self, data_service_id, dataflow_id, raw_json = None, session = None):
        self.data_service_id = data_service_id
        self.dataflow_id = dataflow_id
        self.session = session
        self.prefix = "organizations/{}/projects/{}".format(self.data_service_id, self.dataflow_id)

        if raw_json is None and session is not None:
            raw_json = self.session.get(self.prefix) # to confirm access

    def list_components(self, raw=False):
        """
        List the Components (Connectors and Transforms) in the Dataflow.

        # Returns
        List<Component>: the Components

        # Raises
        HTTPError: on API errors
        """
        raw_resp = self.session.get(self.prefix + "/components")
        if raw:
            return raw_resp

        return list(map(
            lambda c:
                Component(self.data_service_id, self.dataflow_id, c['id'], raw_json=c, session=self.session),
            raw_resp['data']
        ))

    def get_component(self, component_id, raw=False):
        """
        Get a Component from a Dataflow

        # Parameters
        component_id (str): the ID of the Component

        # Returns
        Component: the Component

        # Raises
        HTTPError: on API errors
        """
        raw_list = filter(
            lambda c: c['id'] == component_id,
            self.list_components(raw=True)['data'])
        raw_json = next(raw_list, None)
        if raw_json is None:
            raise KeyError('No component with id: ' + component_id)
        if raw:
            return raw_json

        return Component(
                self.data_service_id,
                self.dataflow_id,
                component_id,
                raw_json=raw_json,
                session=self.session)

    def __repr__(self):
        return '<{2}.{3} {0}.{1}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.__class__.__module__,
            self.__class__.__qualname__)


class Component:
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
    raw_json (dict):
        The API's JSON definition of the Data Service.
        Used, if provided, to construct the DataService directly and avoid one API request.
        (default is `None`)
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """
    def __init__(self, data_service_id, dataflow_id, component_id, raw_json=None, session=None):
        self.data_service_id = data_service_id
        self.dataflow_id = dataflow_id
        self.component_id = component_id
        self.session = session

        if raw_json is None and session is not None:
            df = Dataflow(data_service_id, dataflow_id, session=session)
            raw_json = df.get_component(component_id, raw=True)

        self.component_type = parse_component_type(raw_json)

        self.prefix = "organizations/{}/projects/{}/{}s/{}".format(
            data_service_id, dataflow_id, self.component_type, component_id)

    def get_records(self):
        """
        Get the records of data produced by the Component.

        # Returns
        Iterator<dict>:
            An iterator over the records of data.
            Can be read into a Pandas DataFrame using `Pandas.DataFrame.from_records()`.

        # Raises
        HTTPError: on API errors
        """
        if self.component_type not in ['view', 'source', 'sub', 'pub']:
            raise ValueError("Not able to get records from a {}.".format(type_displayname(self.component_type)))

        return self.session.stream(self.prefix + "/records-stream")

    def __repr__(self):
        return '<{3}.{4} {0}.{1}.{2} type={5}>'.format(
            self.data_service_id,
            self.dataflow_id,
            self.component_id,
            self.__class__.__module__,
            self.__class__.__qualname__,
            type_displayname(self.component_type))