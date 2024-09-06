class Node:
    int8 = True

    def __init__(self, threshold=0, leak=None, delay=None,):
        self.charge = 0
        self.threshold = threshold  # if charge > threshold, fire.
        self.delay = delay
        self.leak = None if leak == -1 else leak  # None or -1 disables leak.
        self.intake = []  # waiting area for incoming spikes to be dealt with.
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
        # count down time for delayed spikes
        self.intake = [(amp, delay - 1) for amp, delay in self.intake]
        # apply leak. charge = 2^(-t/tau) where t is time since last fire.
        if self.leak is not None:
            # WARNING: behavior differs from real caspian here.
            # Tennlab's caspian will not visibly apply leak to charge until the
            # neuron receives a spike of any amplitude (including zero).
            # This code, however, shows the leak being applied regardless.
            self.charge = self.charge * 2 ** (-1 / (2 ** self.leak))
        self.charge = int(self.charge) if self.int8 else self.charge
        # add/integrate charge from spikes if they've just "arrived"
        self.charge += sum([amp for amp, delay in self.intake if delay < 0])
        # and then delete those spikes from cache
        self.intake = [(amp, delay) for amp, delay in self.intake if not delay < 0]

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
        return f"Node at {id(self):x} w/ Threshold: {self.threshold}, Delay: {self.delay}, Leak: {self.leak}, children: {connected}"


class Edge:
    def __init__(self, child, weight, delay: int = 0):
        self.weight = weight
        self.delay = delay
        self.cache = []  # waiting area for delayed spikes: [(amplitude, TTL), ]
        self.output_node = child  # destination for spikes

    def step(self):
        # count down time for delayed spikes (subtract 1 from the TTL of the spike)
        self.cache = [(amp, delay - 1) for amp, delay in self.cache]
        # send spikes whose time has come
        ss = [amp for amp, delay in self.cache if delay < 0]
        self.output_node.intake.append((sum(ss) * self.weight, 0))
        # and then forget only those spikes
        self.cache = [(amp, delay) for amp, delay in self.cache if not delay < 0]


def connect(parent, child, weight, delay=0, **kwargs):
    edge = Edge(child, weight, delay, **kwargs)
    parent.output_edges.append(edge)
    return edge


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
    for i in range(steps):
        step(nodes)


def charges(nodes: list[Node]):
    return [node.charge for node in nodes]


def fires(nodes: list[Node]):
    return [node.fires for node in nodes]


def lastfires(nodes: list[Node]):
    return [node.t_lastfire for node in nodes]


def vectors(nodes: list[Node]):
    return [node.t_fires for node in nodes]


def apply_spike(node, amplitude, delay, int8=True):
    amplitude = int(amplitude * 255) if int8 else amplitude
    # Tennlab neuro translates incoming spike with amp=1.0 to int 255 for some reason.
    node.intake.append((amplitude, delay))


def network_from_json(j: dict):  # read a Tennlab json network and create it.
    def mapping(props: list[dict]):
        return {prop['name']: prop['index'] for prop in props}

    # get mapping of property name to index in 'values' list i.e. m_n['Delay'] -> 1
    # need this because the network json represents the node/edge params as an
    # unordered list i.e. 'values': [127, -1, 0] <-- threshold, leak, delay
    m_n = node_mapping = mapping(j['Properties']['node_properties'])
    m_e = edge_mapping = mapping(j['Properties']['edge_properties'])

    # make nodes from json
    j_nodes = sorted(j['Nodes'], key=lambda v: v['id'])
    nodes = [n['values'] for n in j_nodes]
    nodes = [Node(
        threshold=n[m_n["Threshold"]],
        delay=n[m_n["Delay"]],
        leak=n[m_n["Leak"]],
    ) for n in nodes]

    # make connections from json
    for edge in j['Edges']:
        connect(
            nodes[edge['from']],
            nodes[edge['to']],
            weight=edge['values'][m_e['Weight']],
            delay=edge['values'][m_e['Delay']],
        )

    return nodes


if __name__ == "__main__":
    # import a Tennlab network like so:
    # with open("caspian_network.json") as f:
    #     j = json.loads(f.read())
    # nodes = cap.network_from_json(j)

    # or create one programmatically
    nodes = []
    nodes.append(Node())  # one input
    nodes.append(Node())  # one output

    edge = connect(nodes[0], nodes[1])  # connect them

    print(nodes)

    # send a spike to neuron 0 with amplitude 1 (or 255 like in neuro framework)
    apply_spike(node=nodes[0], amplitude=1.0, delay=0)

    run(nodes, 1)  # run the network for one step

    # if you're using a notebook, this will show a pretty table of the neurons.
    # import tabulate

    # data = zip(
    #     range(len(nodes)),
    #     charges(nodes),
    #     fires(nodes),
    #     lastfires(nodes),
    #     vectors(nodes),
    #     # [node.history for node in nodes],
    # )
    # data = [[
    #     'id',
    #     'charge',
    #     'fires',
    #     't_lastfire',
    #     't_fires',
    #     # 'histories',
    # ]] + list(data)
    # tabulate.tabulate(data, tablefmt='html')
