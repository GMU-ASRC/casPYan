import numba
from numba import int64, float64, typeof
from numba.typed import Dict
from numba.experimental import jitclass

from .network import network_from_json
from .node import NodeBase
from .edge import EdgeBase
from .processor import Processor
from .util import SpikeQueueBase


spike_queue_dict_type = typeof(Dict.empty(key_type=int64, value_type=float64))


@jitclass
class JITSpikeQueue(SpikeQueueBase):
    t: int
    spikes: spike_queue_dict_type

    def __init__(self):
        self.t: int = 0
        spikes = Dict.empty(key_type=int64, value_type=float64)
        self.spikes = spikes

    def __iadd__(self, value):
        self.add_spikes(value.spikes)
        return self

    def ustep(self):
        self.t += 1
        if self.t in self.spikes:
            del self.spikes[self.t]

    def add_spike(self, value: float, time: int = 0):
        if time < 0:
            msg = f"Cannot queue spike {time} time steps in the past to {self}"
            raise ValueError(msg)
        time = int(time)
        time += self.t
        if time in self.spikes:
            self.spikes[time] += value
        else:
            self.spikes[time] = value


class JITNode(NodeBase):

    def __init__(self, threshold=0, leak=None, delay=None,):
        self.charge = 0
        self.threshold = threshold  # if charge > threshold, fire.
        self.delay = int(delay)
        self.leak = None if leak == -1 else leak  # None or -1 disables leak.
        self.intake = JITSpikeQueue()  # waiting area for incoming spikes to be dealt with.
        self.output_edges = []  # outgoing connections
        self.history = []  # record of fire/no fire for each timestep.
        # history may be wiped by external methods.

    def step_fire(self):
        # check if this neuron meets the criteria to fire, and record if it do.
        if self.charge > self.threshold:
            self.fire()
            self.history.append(1)
        else:
            self.history.append(0)

    def step_integrate(self):
        # apply leak. charge = 2^(-t/tau) where t is time since last fire.
        if self.leak is not None:
            # WARNING: behavior differs from real caspian here.
            # Tennlab's caspian will not visibly apply leak to charge until the
            # neuron receives a spike of any amplitude (including zero).
            # This code, however, shows the leak being applied regardless.
            self.charge = self.charge * 2 ** (-1 / (2 ** self.leak))
            self.charge = int(self.charge) if self.int8 else self.charge
        # add/integrate charge from spikes if they've just "arrived"
        self.charge += self.intake.current
        # and then delete those spikes from cache
        self.intake.ustep()

    def fire(self):
        for edge in self.output_edges:
            edge.cache.add_spike(1.0, edge.delay)
        self.charge = 0  # reset charge


class JITEdge(EdgeBase):

    def __init__(self, child, weight, delay: int = 0):
        self.weight = weight
        self.delay = delay
        self.cache = JITSpikeQueue()
        self.output_node = child

    def step(self):
        # send spikes whose time has come
        self.output_node.intake.add_spike(self.cache.current * self.weight, 0)
        # count down and then forget those spikes
        self.cache.ustep()


class JITProcessor(Processor):
    # int8 = True
    # nodes: list[JITNode]
    # inputs: list[JITNode]
    # outputs: list[JITNode]
    # names: list[str]
    # data: dict[str, Any]
    # properties: dict[str, Any]

    def load_json(self, json_dict):
        node_dict, self.inputs, self.outputs = network_from_json(
            json_dict,
            nodetype=JITNode,
            edgetype=JITEdge
        )
        self.names = list(node_dict.keys())
        self.nodes = list(node_dict.values())
        self.data = json_dict.get("Associated_Data", {})
        self.properties = json_dict.get("Properties", {})

    def apply_spikes(self, spikes_per_node):
        for node, spikes in zip(self.inputs, spikes_per_node):
            for value, time in spikes:
                node.intake.add_spike(value, time)
