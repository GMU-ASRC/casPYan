from __future__ import annotations

from collections import namedtuple
from .edge import Edge
from .node import Node

NetworkSegment = namedtuple('NetworkSegment', [
    'nodes',
    'inputs',
    'outputs',
])

DEFAULT_DATA = {
    "Associated_Data": {
        "application": {
        },
        "label": None,
        "processor": {
            "Leak_Enable": True,
            "Max_Leak": 4,
            "Min_Leak": -1,
            "Max_Weight": 127,
            "Min_Weight": -127,
            "Max_Threshold": 127,
            "Min_Threshold": 0,
            "Max_Synapse_Delay": 255,
            "Min_Synapse_Delay": 0,
            "Max_Axon_Delay": 0,
            "Min_Axon_Delay": 0,
        }
    }
}

DEFAULT_NETWORK_PROPERTIES = {"network_properties": []}

DEFAULT_NODE_PROPERTIES = {"node_properties": [
    {
        "index": 0,
        "name": "Threshold",
        "max_value": 127.0,
        "min_value": 0.0,
        "size": 1,
        "type": 73
    },
    {
        "index": 1,
        "name": "Leak",
        "max_value": 4.0,
        "min_value": -1.0,
        "size": 1,
        "type": 73
    },
    {
        "index": 2,
        "name": "Delay",
        "max_value": 0.0,
        "min_value": 0.0,
        "size": 1,
        "type": 73
    },
]}

DEFAULT_EDGE_PROPERTIES = {"edge_properties": [
    {
        "index": 0,
        "name": "Weight",
        "max_value": 127.0,
        "min_value": -127.0,
        "size": 1,
        "type": 73
    },
    {
        "index": 1,
        "name": "Delay",
        "max_value": 300.0,
        "min_value": 0.0,
        "size": 1,
        "type": 73
    },
]}

DEFAULT_CASPIAN_PROPERTIES = {"Properties": {
    **DEFAULT_NETWORK_PROPERTIES,
    **DEFAULT_NODE_PROPERTIES,
    **DEFAULT_EDGE_PROPERTIES
}}


def get_key(dict_view, item):
    for key, value in dict_view:
        if value == item:
            return key  # this isn't optimal but whatever


def connect(parent, child, weight=0, delay=0, exist_ok=True, **kwargs):
    new_edge = Edge(child, weight, delay, **kwargs)

    duplicates = [edge for edge in parent.output_edges if edge.output_node == child]
    if any(duplicates):
        if exist_ok == 'add':
            pass  # continue to add the duplicate edge
        elif exist_ok:  # remove duplicates
            parent.output_edges = [edge for edge in parent.output_edges if edge.output_node != child]
        else:
            raise ValueError(f"Edge already exists between {parent} and {child}:\nexisting: {duplicates}\nnew: {new_edge}")  # noqa: EM102

    parent.output_edges.append(new_edge)
    return new_edge


def make_layer(n) -> list[Node]:
    return [Node() for _ in range(n)]


def step(nodes):
    # do a single time tick
    # first, have all nodes try to fire
    for node in nodes:
        node.step_fire()
    # then, have those spikes be sent or delayed to their destinations
    for node in nodes:
        for edge in node.output_edges:
            edge.step()
    # finally, have nodes add received spikes to their charge (and apply leak).
    for node in nodes:
        node.step_integrate()


def run(nodes: list[Node], steps: int):
    for node in nodes:  # clear histories. Tennlab does this each run()
        node.history = []
    for _i in range(steps):
        step(nodes)


def charges(nodes: list[Node]):
    return [node.charge for node in nodes]


def fires(nodes: list[Node]):
    return [node.fires for node in nodes]


def lastfires(nodes: list[Node]):
    return [node.t_lastfire for node in nodes]


def vectors(nodes: list[Node]):
    return [node.t_fires for node in nodes]


def network_from_json(j: dict) -> tuple[dict[int, Node], list[Node], list[Node]]:
    # read a Tennlab json network and create it.
    def mapping(props: list[dict]):
        return {prop['name']: prop['index'] for prop in props}

    # get mapping of property name to index in 'values' list i.e. m_n['Delay'] -> 1
    # need this because the network json represents the node/edge params as an
    # unordered list i.e. 'values': [127, -1, 0] <-- threshold, leak, delay
    m_n = _node_mapping = mapping(j['Properties']['node_properties'])
    m_e = _edge_mapping = mapping(j['Properties']['edge_properties'])

    # make nodes from json
    j_nodes = sorted(j['Nodes'], key=lambda v: v['id'])
    nodes = [(n['id'], n['values']) for n in j_nodes]
    nodes = {idx: Node(
        threshold=v[m_n["Threshold"]],
        delay=v[m_n["Delay"]],
        leak=v[m_n["Leak"]],
    ) for idx, v in nodes}

    # make connections from json
    for edge in j['Edges']:
        connect(
            nodes[edge['from']],
            nodes[edge['to']],
            weight=edge['values'][m_e['Weight']],
            delay=edge['values'][m_e['Delay']],
        )

    inputs = [nodes[i] for i in j['Inputs']]
    outputs = [nodes[i] for i in j['Outputs']]
    return NetworkSegment(nodes, inputs, outputs)
    # node is a dict so as to preserve the ids
    # use list(nodes.values()) to make it a list for casPYan functions


def to_tennlab(
    nodes,
    inputs,
    outputs,
    data=DEFAULT_DATA,  # use {} instead of None
    properties: dict = DEFAULT_CASPIAN_PROPERTIES,
) -> dict:
    d = {}

    if isinstance(nodes, list):
        nodes = dict(enumerate(nodes)).items()
    elif isinstance(nodes, dict):
        nodes = nodes.items()

    def mapping(props: list[dict]):
        return {prop['index']: prop['name'] for prop in props}

    def node_dict(node):
        delay, leak = node.delay, node.leak
        return {
            'Threshold': node.threshold,
            'Delay': 0 if delay is None else delay,
            'Leak': -1 if leak is None else leak
        }

    def edge_dict(edge):
        return {
            'Weight': edge.weight,
            'Delay': edge.delay
        }

    m_n = _node_mapping = mapping(properties['Properties']['node_properties'])
    m_e = _edge_mapping = mapping(properties['Properties']['edge_properties'])

    j_nodes = [
        {
            'id': i,
            'values': [
                node_dict(node)[m_n[0]],
                node_dict(node)[m_n[1]],
                node_dict(node)[m_n[2]]
            ]
        }
        for i, node in nodes
    ]

    def edges(nodes):
        for parent_id, node in nodes:
            for edge in node.output_edges:
                yield parent_id, get_key(nodes, edge.output_node), edge

    j_edges = [
        {
            'from': parent_id,
            'to': child_id,
            'values': [
                edge_dict(edge)[m_e[0]],
                edge_dict(edge)[m_e[1]],
            ]
        }
        for parent_id, child_id, edge in edges(nodes)
    ]

    input_ids = [get_key(nodes, node) for node in inputs]
    output_ids = [get_key(nodes, node) for node in outputs]

    d.update(data)
    d.update(properties)
    d.update({'Nodes': j_nodes})
    d.update({'Inputs': input_ids})
    d.update({'Outputs': output_ids})
    d.update({'Edges': j_edges})
    d.update({'Network_Values': []})

    return d


class TennNetProxy:
    def __init__(self, net=None):
        self.nodes = None
        self.inputs = None
        self.outputs = None
        self.net = net

    def from_json(self, j):
        self.nodes, self.inputs, self.outputs = network_from_json(j)
        self.net = j

    def get_data(self, key):
        return self.net['Associated_Data'][key]

    def set_data(self, key, value):
        self.net['Associated_Data'][key] = value

    def to_str(self):
        import json
        return json.dumps(self.net)