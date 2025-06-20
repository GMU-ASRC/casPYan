from __future__ import annotations

from .network import connect, make_layer

# typing
# from .edge import Edge
from .node import Node


def connect_multiple(parent: Node, children: list[Node]):
    for child in children:
        connect(parent, child)


def fully_connect_layers(parents: list[Node], children: list[Node]):
    for parent in parents:
        connect_multiple(parent, children)


def feedforward_fc(
    n_inputs: int,
    n_outputs: int,
    n_hidden_layers: list | None = None,
):
    inputs: list[Node] = make_layer(n_inputs)
    outputs: list[Node] = make_layer(n_outputs)
    if n_hidden_layers is None:
        n_hidden_layers = []
    hidden_layers: list[list[Node]] = [make_layer(n) for n in n_hidden_layers]

    # make connections
    if not hidden_layers:
        fully_connect_layers(inputs, outputs)
    else:
        fully_connect_layers(inputs, hidden_layers[0])
        fully_connect_layers(hidden_layers[-1], outputs)
        # make connections between hidden layers
        layer = iter(hidden_layers)
        a = next(layer, None)
        while a is not None:
            b = next(layer, None)
            if b is None:
                break
            fully_connect_layers(a, b)
            a = b

    return inputs, outputs, hidden_layers


def flatten_ff(inputs, outputs, hidden_layers):
    flat_hidden_neurons = sum(hidden_layers, [])
    network = inputs + outputs + flat_hidden_neurons
    return network
