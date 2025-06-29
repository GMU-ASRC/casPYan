# casPYan

A Python implementation of the Caspian SNN processor simulator.

## Installation

```bash
pip install caspyan
```

## Usage

```python
import casPYan
```

### Loading a Caspian network

```python
# load a network from a json file
import json
with open("network.json") as f:
    network = json.load(f)

# Create a processor and load the network into it
processor = casPYan.Processor()
processor.load_network(network)
```

### Setting up Encoders and Decoders

```python
import casPYan.ende.rate as ende

# Create encoder and decoder arrays
encoders = [
    ende.RateEncoder(interval=10, domain=[0.0, 1.0])
    for _ in processor.inputs
]
decoders = [
    ende.RateDecoder(interval=10, domain=[0.0, 1.0])
    for _ in processor.outputs
]
```

### Running a Caspian processor

```python
input_vector = [0.5, 1.0]

# encode to spikes
spikes = [enc.get_spikes(x) for enc, x in zip(encoders, input_vector)]

# apply spikes
processor.apply_spikes(spikes)
# run processor for 10 ticks
processor.run(10)

# decode spikes to floats
data = [dec.decode(node.history) for dec, node in zip(decoders, processor.outputs)]
```

### Saving a Caspian network

```python
network = processor.to_tennlab()
with open("network.json", "w") as f:
    json.dump(network, f)
```

### Creating a Caspian network from scratch

The low-level representation of a Caspian network is a list of nodes,
along with a list of inputs and outputs that reference those nodes.

```python
nodes = []

nodes.append(casPYan.Node(threshold=0.5, delay=0.0, leak=0.0))
nodes.append(casPYan.Node(threshold=1.0, delay=0.0, leak=0.0))

inputs = [nodes[0]]
outputs = [nodes[1]]

casPYan.connect(nodes[0], nodes[1], weight=0.5, delay=0)

casPYan.run(nodes, 10)

spikes = [node.history for node in outputs]

# saving and loading node representations
json_dict = casPYan.to_tennlab(nodes, inputs, outputs)
# json_dict is a Python dict that can be saved to a json file
# It is similar to what is loaded by casPYan.network_from_json
nodes, inputs, outputs = casPYan.network_from_json(json_dict)
```

See the following files for more low-level functions:

- `casPYan/node.py`
- `casPYan/edge.py`
- `casPYan/network.py`

## Disclaimer

This software does not guarantee the correctness of the simulation in relation to
the original Caspian SNN simulator, Caspian processors, or any other software.

casPYan is not a substitute for the original software, and it is not supported by
the original authors.

It should not be thought of as a port.
