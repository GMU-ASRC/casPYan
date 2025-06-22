from __future__ import annotations

from .util import SpikeQueue


class Edge:
    def __init__(self, child, weight, delay: int = 0):
        self.weight = weight
        self.delay = delay
        self.cache = SpikeQueue()  # waiting area for delayed spikes: [(amplitude, TTL), ]
        self.output_node = child  # destination for spikes

    def step(self):
        # send spikes whose time has come
        self.output_node.intake.add_spike(sum(self.cache[0]) * self.weight, 0)
        # count down and then forget those spikes
        self.cache.step()

    def __repr__(self):
        output = f"{id(self.output_node):x}"[-4:]
        return f"{self.__class__} at {id(self):x} w/ Weight: {self.weight}, Delay: {self.delay}, To: {output}"
