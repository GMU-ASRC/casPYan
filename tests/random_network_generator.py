import numpy as np
import casPYan
import caspian
import neuro


class CaspyanNetworkGenerator:
    WEIGHT_RANGE = (-127, 127)
    THRESHOLD_RANGE = (0.0, 127.0)
    DELAY_RANGE = (0, 255)
    LEAK_RANGE = (-1, 4)

    def __init__(self, n_nodes, n_inputs, n_outputs,
                 density=0.2, rng: int | np.random.Generator | None = None):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        self.n = n_nodes
        self.density = density
        self.seed = rng
        self.nodes = []
        self.proc = None
        self._seed = None
        self.int8 = True

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, value=None):
        if value is None:
            import sys
            value = np.random.default_rng().integers(0, sys.maxsize)
        elif isinstance(np.random.Generator):
            self._seed = None
            self.rng = value
            return

        self._seed = value
        self.rng = np.random.default_rng(self._seed)

    def generate_weights(self):
        return self.rng.integers(*self.WEIGHT_RANGE, size=(self.n, self.n), endpoint=True)

    def generate_mask(self):
        return self.rng.choice([1, 0], size=(self.n, self.n), p=[self.density, 1 - self.density])

    def generate_masked_weights(self):
        return self.generate_weights() * self.generate_mask()

    def generate_nodes(self, apply=False):
        if self.int8:
            def thresh_gen():
                thresh_range = np.asarray(self.THRESHOLD_RANGE).astype(np.int8)
                return self.rng.integers(*thresh_range, endpoint=True)
        else:
            def thresh_gen():
                return self.rng.uniform(*self.THRESHOLD_RANGE)

        nodes = [
            casPYan.Node(
                threshold=thresh_gen(),
                delay=0,
                leak=self.rng.integers(*self.LEAK_RANGE),
            )
            for _ in range(self.n)
        ]
        if apply:
            self.nodes = nodes
        return nodes

    def apply_weights(self, weights=None):
        if weights is None:
            weights = self.generate_masked_weights()
        for i, j in zip(*weights.nonzero()):
            casPYan.connect(self.nodes[i], self.nodes[j],
                            weight=float(weights[i, j]),
                            delay=int(self.rng.integers(*self.DELAY_RANGE)))

    def make_network(self):
        self.generate_nodes(apply=True)
        self.apply_weights()
        self.proc = casPYan.Processor()
        self.proc.nodes = self.nodes
        self.proc.inputs = self.nodes[:self.n_inputs]
        self.proc.outputs = self.nodes[-self.n_outputs:]
        return self.proc

    def generate_spikes(self, t=1, value_range=(0.0, 1.0), choices=None, rng=None):
        if rng is None:
            rng = self.rng
        return random_spikes(self.n, t=t, value_range=value_range, choices=choices, rng=rng)

    def proc_as_caspian(self):
        if self.proc is None:
            self.make_network()
        cnet = neuro.Network()
        cnet.from_json(self.proc.to_tennlab())
        cproc = caspian.Processor(cnet.get_data("processor"))
        cproc.load_network(cnet)
        cproc.track_neuron_events(True)
        return cproc


def random_spikes(n, t=1, value_range=(0.0, 1.0), choices=None, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    if isinstance(n, int):
        n = range(n)
    if choices is None:
        for _i in n:
            yield [(float(v), i) for i, v in enumerate(rng.uniform(*value_range, t))]
    else:
        for _i in n:
            yield [(float(v), i) for i, v in enumerate(rng.choice(choices, t))]


def spike_py2c(spikes: list[list[tuple[float, int]]]):
    return [neuro.Spike(id=nid, time=t, value=v / 255) for nid, n_spikes in enumerate(spikes) for v, t in n_spikes]
