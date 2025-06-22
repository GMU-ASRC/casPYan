from __future__ import annotations

from .util import NONCE1, SpikeQueue


class Node:
    int8 = True

    def __init__(self, threshold=0, leak=None, delay=None,):
        self.charge = 0
        self.threshold = threshold  # if charge > threshold, fire.
        self.delay = delay
        self.leak = None if leak == -1 else leak  # None or -1 disables leak.
        self.intake = SpikeQueue()  # waiting area for incoming spikes to be dealt with.
        self.output_edges = []  # outgoing connections
        self.history = []  # record of fire/no fire for each timestep.
        # history may be wiped by external methods.

        self.callback_prestep_fire = NONCE1
        self.callback_prestep_integrate = NONCE1

    def step_fire(self):
        # check if this neuron meets the criteria to fire, and record if it do.
        self.callback_prestep_fire(self)
        if self.charge > self.threshold:
            self.fire()
            self.history.append(1)
        else:
            self.history.append(0)

    def step_integrate(self):
        self.callback_prestep_integrate(self)
        # apply leak. charge = 2^(-t/tau) where t is time since last fire.
        if self.leak is not None:
            # WARNING: behavior differs from real caspian here.
            # Tennlab's caspian will not visibly apply leak to charge until the
            # neuron receives a spike of any amplitude (including zero).
            # This code, however, shows the leak being applied regardless.
            self.charge = self.charge * 2 ** (-1 / (2 ** self.leak))
            self.charge = int(self.charge) if self.int8 else self.charge
        # add/integrate charge from spikes if they've just "arrived"
        self.charge += sum(self.intake[0])
        # and then delete those spikes from cache
        self.intake.step()

    def fire(self):
        for edge in self.output_edges:
            edge.cache.append([1.0, edge.delay])
        self.charge = 0  # reset charge

    @property
    def fires(self):  # the number of fires from this neuron ever
        return sum([bool(x) for x in self.history])

    @property
    def t_lastfire(self):  # get index of most recent fire
        for i in reversed(range(len(self.history))):
            if self.history[i]:
                return i
        return -1.0  # if no fires in history, return -1

    @property
    def t_fires(self):  # indexes of fires
        return [i for i, fired in enumerate(self.history) if fired]

    def __repr__(self):
        connected = [f"{id(e.output_node):x}"[-4:] for e in self.output_edges]
        return f"Node at {id(self):x} w/ Threshold: {self.threshold}, Delay: {self.delay}, Leak: {self.leak}, children: {connected}"  # noqa


def apply_spike(node, amplitude, delay, int8=True):
    amplitude = int(amplitude * 255) if int8 else amplitude
    # Tennlab neuro translates incoming spike with amp=1.0 to int 255 for some reason.
    node.intake.append((amplitude, delay))
