import casPYan
import casPYan.ende.rate as ende

nodes = []

#A and B inputs
nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))
nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))

#OR output
nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))
#AND ouput
nodes.append(casPYan.Node(threshold = 1.0, delay=0.0, leak=0.0))


#OR synapses
casPYan.connect(nodes[0], nodes[2], weight = 1.0, delay=0.0)
casPYan.connect(nodes[1], nodes[2], weight = 1.0, delay=0.0)

#AND synapses
casPYan.connect(nodes[0], nodes[3], weight = 1.0, delay=0.0)
casPYan.connect(nodes[1], nodes[3], weight = 1.0, delay=0.0)


inputs = [nodes[0], nodes[1]]
outputs = [nodes[2], nodes[3]]

processor = casPYan.Processor()
processor.nodes = nodes
processor.inputs = inputs
processor.outputs = outputs

spikes = [
    [ (0, 0), (1, 2), (0, 4), (1, 6) ],
    [ (0, 0), (0, 2), (1, 4), (1, 6) ]
]
processor.apply_spikes(spikes)
processor.run(9)

#Horizontal print
print("a input   ", processor.inputs[0].history)
print("b input   ", processor.inputs[1].history)
print("OR output ", processor.outputs[0].history)
print("AND output", processor.outputs[1].history)

#Alternative vertical print
print(*list(zip(processor.inputs[0].history, processor.inputs[1].history, processor.outputs[0].history, processor.outputs[1].history)), sep="\n")