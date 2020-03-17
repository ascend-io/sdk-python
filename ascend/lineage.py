"""
Module for deriving the component lineage
"""

import abc
import networkx as nx
from dataclasses import dataclass
from ascend.model import Component, Dataflow, component_from_json
from typing import List, Optional


@dataclass(eq=True, frozen=True)
class NxNode(abc.ABC):
    @property
    @abc.abstractmethod
    def component_nx_node(self):
        pass

    @abc.abstractmethod
    def short_name(self):
        pass


@dataclass(eq=True, frozen=True)
class ComponentNxNode(NxNode):
    uuid: str
    @property
    def component_nx_node(self):
        return self

    def short_name(self):
        return self.uuid[:10]


@dataclass(eq=True)
class ComponentDetails:
    component: Component
    schema: list
    expression: str


@dataclass(eq=True, frozen=True)
class ColumnNxNode(NxNode):
    name: str
    component: ComponentNxNode

    @property
    def component_nx_node(self):
        return self.component

    def short_name(self):
        return self.component.short_name() + '.' + self.name

@dataclass(eq=True, frozen=True)
class Position:
    index: int
    line: int
    col: int
    @staticmethod
    def from_json(json):
        if not json:
            return None
        return Position(json.get('index', 0), json.get('line', 0), json.get('column', 0))


@dataclass(eq=True, frozen=True)
class Selection:
    start: Position
    end: Position
    @staticmethod
    def from_json(json):
        if not json:
            return None
        return Selection(start=Position.from_json(json.get('start')),
                         end=Position.from_json(json.get('end')))

@dataclass
class ColumnDetails:
    expression: str
    selection: Optional[Selection]

@dataclass(eq=True, frozen=True)
class NxEdge:
    expression: str
    type: str
    selection: Optional[Selection]


@dataclass
class Node(abc.ABC):
    @property
    @abc.abstractmethod
    def nx_node(self) -> NxNode:
        pass

    @property
    @abc.abstractmethod
    def get_component(self) -> Component:
        pass

    @property
    @abc.abstractmethod
    def get_component_node(self):
        pass

    def __hash__(self):
        return hash(self.nx_node) + hash(type(self))


@dataclass
class ComponentNode(Node):
    component: Component
    schema: list
    expression: str

    @property
    def nx_node(self):
        return ComponentNxNode(self.component.uuid)

    @property
    def get_component(self):
        return self.component

    @property
    def get_component_node(self):
        return self

    def __repr__(self):
        return self.component.component_id

    def __hash__(self):
        return super().__hash__()


@dataclass
class ColumnNode(Node):
    component_node: ComponentNode
    name: str
    expression: str
    selection: Optional[Selection]

    @property
    def nx_node(self):
        return ColumnNxNode(component=self.component_node.nx_node, name=self.name)

    @property
    def get_component(self):
        return self.component_node.component

    @property
    def get_component_node(self):
        return self.component_node

    def __repr__(self):
        return str(self.component_node) + '.' + self.name

    def __hash__(self):
        return super().__hash__()

@dataclass(eq=True, frozen=True)
class Edge:
    start: Node
    end: Node
    expression: str
    selection: Optional[Selection]
    type: str


class LineageGraph:
    """
    A LineageGraph models connections between components and columns

    # Parameters
    session (ascend.session.Session):
        The client session used for HTTP requests.

    # Raises
    HTTPError: on API errors
    """
    def __init__(self, session):
        self.session = session
        self.uuid_to_component = {}  # cache components
        self.lineage = nx.MultiDiGraph()
        self.lineage_loaded = set()
        self.dataflows_loaded = set()

    def _ensure_component_loaded(self, component: Component):
        if component.uuid not in self.uuid_to_component:
            self._ensure_dataflow_loaded(component.data_service_id, component.dataflow_id)

    def get_lineage(self, comp):
        try:
            return self.session.get(f'{comp.resource_path}/lineage')
        except:
            print(f'Unable to retrieve lineage for {comp}')
            raise

    def _load_dataflow(self, dataflow: Dataflow):
        comps = dataflow.list_components()
        for comp in comps:
            self.uuid_to_component[comp.uuid] = comp

    def _ensure_dataflow_loaded(self, data_service_id, dataflow_id):
        """
        Ensure we have loaded the designated dataflow
        """
        t = (data_service_id, dataflow_id)
        if t not in self.dataflows_loaded:
            dataflow = Dataflow(data_service_id, dataflow_id, None, self.session)
            self._load_dataflow(dataflow)
            self.dataflows_loaded.add(t)

    def _ensure_lineage_loaded(self, component: Component):
        self._ensure_component_loaded(component)
        if component.api_type == 'pub':
            self._ensure_lineage_loaded(
                self.uuid_to_component[component.json_definition['inputUUID']])
        elif component.api_type == 'sub':
            pub, = self._input_components(component)
            self._ensure_lineage_loaded(pub)
        elif component.uuid not in self.lineage_loaded:
            comp = self.uuid_to_component[component.uuid]
            lin = self.get_lineage(comp).get('data', {})
            comps = []
            cols = []
            for component_node in lin.get('component_nodes') or ():
                node_uuid = component_node.get('uuid')
                dataflow_id = component_node.get('data_flow_id')
                data_service_id = component_node.get('data_service_id')
                self._ensure_dataflow_loaded(data_service_id, dataflow_id)
                comp = ComponentNxNode(node_uuid)
                comps.append(comp)
                if comp not in self.lineage:
                    node_component = self.uuid_to_component[node_uuid]
                    schema = component_node.get('schema')
                    exp = component_node.get('expression', '<missing>')
                    details = ComponentDetails(node_component, schema, exp)
                    self.lineage.add_node(comp, details=details)
            for column_node in lin.get('column_nodes') or ():
                name = column_node.get('name')
                comp_idx = column_node.get('component_node_index', 0)
                col = ColumnNxNode(name, comps[comp_idx])
                cols.append(col)
                if col not in self.lineage:
                    exp = column_node.get('expression', '<missing>')
                    position = Selection.from_json(
                        column_node.get('component_expression_selection', None))
                    details = ColumnDetails(exp, position)
                    self.lineage.add_node(col, details=details)
            for edge in lin.get('component_edges') or ():
                start = edge.get('input', 0)
                end = edge.get('output', 0)
                exp = edge.get('expression', '<missing>')
                position = Selection.from_json(edge.get('output_expression_selection', None))
                edge = NxEdge(exp, '', position)
                self._connect_components(comps[start], comps[end], edge)
            for edge in lin.get('column_edges') or ():
                start = edge.get('input', 0)
                inf = edge.get('Type')
                t = list(inf.keys())[0] if inf else 'Unknown'
                output_type = edge.get('Output')
                k, v = list(output_type.items())[0]
                if k == 'OutputComponent':
                    output = comps[v]
                else:
                    output = cols[v]
                position = Selection.from_json(
                    edge.get('output_component_expression_selection', None))
                exp = edge.get('expression', '')
                nx_edge = NxEdge(exp, t, position)
                self._connect_nodes(cols[start], output, nx_edge)
            self.lineage_loaded.add(component.uuid)

    def _setup_lineage(self, component: Component = None, column: str = None,
                       node: Node = None) -> NxNode:
        if component is None:
            component = node.component
        self._ensure_lineage_loaded(component)
        if node is None:
            comp_node = ComponentNxNode(component.uuid)
            if column is not None:
                node = ColumnNxNode(component=comp_node, name=column)
            else:
                node = comp_node
        return node


    def _input_components(self, component: Component):
        """
        :param component: Component
        :return: list of input components
        """
        self._ensure_component_loaded(component)
        if component.api_type == 'view':
            uuids = [e['uuid'] for e in component.json_definition['inputs']]
        elif component.api_type in ['sink', 'pub']:
            uuids = [component.json_definition['inputUUID']]
        elif component.api_type == 'sub':
            # check if we need substitute a data feed for a sub
            pubUUID = component.json_definition['pubUUID']
            # need to load pubs manually since they are not part of the dataflow
            if pubUUID not in self.uuid_to_component:
                payload = self.session.get(f'{component.resource_api_path}/pub')['data']
                pub = component_from_json(payload, component.session)
                self._ensure_component_loaded(pub)
            uuids = [pubUUID]
        else:
            raise Exception(f'unkown component {component}')
        return list(map(self.uuid_to_component.get, uuids))

    # potentially add a DataFeed node and all associated columns
    def _connect_components(self, start_node: ComponentNxNode, end_node: ComponentNxNode, edge):
        node_details = nx.get_node_attributes(self.lineage, 'details')
        start = node_details[start_node].component
        end = node_details[end_node].component
        if start.dataflow_id == end.dataflow_id:
            self.lineage.add_edge(start_node, end_node, edge)
        else:
            self._ensure_component_loaded(end)
            sub, = self._input_components(end)
            pub = self.uuid_to_component[sub.json_definition['pubUUID']]
            pub_node = ComponentNxNode(pub.uuid)
            if pub_node not in self.lineage:
                start_details = node_details[start_node]
                pub_details = ComponentDetails(
                    component=pub, schema=start_details.schema, expression='Identity')
                self.lineage.add_node(pub_node, details=pub_details)
                for column in node_details[start_node].schema:
                    name, _ = column.split(' ')
                    start_col = ColumnNxNode(name=name, component=start_node)
                    end_col = ColumnNxNode(name=name, component=pub_node)
                    col_details = node_details[start_col]
                    self.lineage.add_node(end_col, details=col_details)
                    self.lineage.add_edge(start_col, end_col, NxEdge('DataFeed', None, None))
                self.lineage.add_edge(start_node, pub_node, NxEdge('DataFeed', None, None))
            self.lineage.add_edge(pub_node, end_node, edge)

    # potentially route through existing DataFeed node
    def _connect_nodes(self, start_node: ColumnNxNode, end_node: NxNode, edge):
        node_details = nx.get_node_attributes(self.lineage, 'details')
        start_comp = node_details[start_node.component].component
        end_comp = node_details[end_node.component_nx_node].component
        if start_comp.dataflow_id == end_comp.dataflow_id:
            self.lineage.add_edge(start_node, end_node, edge)
        else:
            pub_node, = filter(lambda x: isinstance(x, ComponentNxNode),
                               self.lineage.predecessors(end_node.component_nx_node))
            pub_col = ColumnNxNode(name=start_node.name, component=pub_node)
            self.lineage.add_edge(pub_col, end_node, edge)

    def make_node(self, nx_node: NxNode = None, component: Component = None,
                  column: str = None) -> Node:
        if component is None:
            component = self.uuid_to_component[nx_node.component_nx_node.uuid]
        self._ensure_lineage_loaded(component)
        if nx_node is None:
            nx_node = ComponentNxNode(component.uuid)
            if column is not None:
                nx_node = ColumnNxNode(component=nx_node, name=column)
        details_dict = nx.get_node_attributes(self.lineage, 'details')
        details = details_dict[nx_node.component_nx_node]
        component_node = ComponentNode(component=component, schema=details.schema,
                                       expression=details.expression)
        if isinstance(nx_node, ColumnNxNode):
            col_details = details_dict[nx_node]
            return ColumnNode(component_node=component_node, name=nx_node.name,
                              expression=col_details.expression, selection=col_details.selection)
        else:
            return component_node

    def predecessors(self, component: Component) -> List[Component]:
        """
        Get inputs to the provided Component.

        # Parameters
        component (Component): Component to get inputs for

        # Returns
        List<Component>: List of input Components

        # Raises
        HTTPError: on API errors
        """
        self._ensure_lineage_loaded(component)
        nx_node = ComponentNxNode(component.uuid)
        return [
            self.uuid_to_component.get(n.uuid) for n in self.lineage.predecessors(nx_node)
            if isinstance(n, ComponentNxNode)
        ]

    def successors(self, component: Component) -> List[Component]:
        """
        Get outputs from component

        # Parameters
        component (Component): Component to get outputs for

        # Returns
        List<Component>: List of output Components

        # Raises
        HTTPError: on API errors
        """
        self._ensure_lineage_loaded(component)
        nx_node = ComponentNxNode(component.uuid)
        return [
            self.uuid_to_component.get(n.uuid) for n in self.lineage.successors(nx_node)
            if isinstance(n, ComponentNxNode)
        ]

    def in_edges(self, component: Component = None, column: str = None,
                 node: Node = None) -> List[Edge]:
        end_nx = self._setup_lineage(component, column, node)
        end = self.make_node(end_nx)
        ret = []
        if end_nx in self.lineage:
            for pred_nx in self.lineage.predecessors(end_nx):
                start = self.make_node(pred_nx)
                for edge in self.lineage.get_edge_data(pred_nx, end_nx).keys():
                    ret.append(Edge(start=start, end=end, expression=edge.expression,
                                    selection=edge.selection, type=edge.type))
        return ret

    def out_edges(self, component: Component = None, column: str = None,
                  node: Node = None) -> List[Edge]:
        start_nx = self._setup_lineage(component, column, node)
        start = self.make_node(start_nx)
        ret = []
        if start_nx in self.lineage:
            for succ in self.lineage.successors(start_nx):
                end = self.make_node(succ)
                for edge in self.lineage.get_edge_data(start_nx, succ).keys():
                    ret.append(Edge(start=start, end=end, expression=edge.expression,
                                    selection=edge.selection, type=edge.type))
        return ret

    def columns(self, component):
        self._ensure_lineage_loaded(component)
        return [
            self.make_node(n) for n in self.lineage.nodes()
            if type(n) is ColumnNxNode and n.component.uuid == component.uuid
        ]
