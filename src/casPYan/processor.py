from .network import step, run, charges, fires, lastfires, vectors, network_from_json


class Processor:
    def __init__(self, caspian_params=None, ):
        self.nodes = []
        self.inputs = []
        self.outputs = []

    def load_json(self, json):
        self.nodes, self.inputs, self.outputs = network_from_json(json)

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
