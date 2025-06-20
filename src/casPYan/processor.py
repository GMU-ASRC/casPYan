from __future__ import annotations

import json

from .network import step, run, charges, fires, lastfires, vectors, network_from_json
from .network import to_tennlab, DEFAULT_DATA, DEFAULT_NETWORK_PROPERTIES

from typing import Any


class Processor:
    def __init__(self, caspian_params=None, ):
        self.nodes = []
        self.inputs = []
        self.outputs = []
        self.names = []
        self.data: dict[str, Any] = {}
        self.properties: dict[str, Any] = {}

    def load_network(self, network):
        if not isinstance(network, dict):
            network = network.to_str()
            network = json.loads(network)
        self.load_json(network)

    def load_json(self, json_dict):
        node_dict, self.inputs, self.outputs = network_from_json(json_dict)
        self.names = list(node_dict.keys())
        self.nodes = list(node_dict.values())
        self.data = json_dict.get("Associated_Data", {})
        self.properties = json_dict.get("Properties", {})

    def to_tennlab(self, data=None, properties=None):
        if data is None:
            data = DEFAULT_DATA if self.data == {} else self.data
        if properties is None:
            properties = DEFAULT_NETWORK_PROPERTIES if self.properties == {} else self.properties
        return to_tennlab(self.nodes, self.inputs, self.outputs, data, properties)

    def get_data(self, key):
        return self.data.get(key, None)

    def apply_spikes(self, spikes_per_node):
        for node, spikes in zip(self.inputs, spikes_per_node):
            node.intake += spikes

    def step(self):
        step(self.nodes)

    def run(self, steps: int):
        run(self.nodes, steps)

    def charges(self):
        return charges(self.nodes)

    def fires(self):
        return fires(self.nodes)

    def lastfires(self):
        return lastfires(self.nodes)

    def vectors(self):
        return vectors(self.nodes)

    def neuron_counts(self):
        return [node.fires for node in self.nodes]
