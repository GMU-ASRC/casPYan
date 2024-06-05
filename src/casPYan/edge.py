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
