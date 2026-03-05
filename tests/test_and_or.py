import unittest
import casPYan as casPYan


class AndOrTest(unittest.TestCase):
    def test_and(self):
        print("\nTEST AND")
        nodes = []

        #A and B inputs
        nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))
        nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))

        #AND ouput
        nodes.append(casPYan.Node(threshold = 1.0, delay=0.0, leak=0.0))

        #AND synapses
        casPYan.connect(nodes[0], nodes[2], weight = 1.0, delay=0.0)
        casPYan.connect(nodes[1], nodes[2], weight = 1.0, delay=0.0)


        inputs = [nodes[0], nodes[1]]
        outputs = [nodes[2]]

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

        expected = [0, 0, 0, 0, 0, 0, 0, 0, 1]

        #Horizontal print
        print("a input   ", processor.inputs[0].history)
        print("b input   ", processor.inputs[1].history)
        print("AND output", processor.outputs[0].history)

        assert processor.outputs[0].history == expected

    def test_or(self):
        print("\nTEST OR")
        nodes = []

        #A and B inputs
        nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))
        nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))

        #OR output
        nodes.append(casPYan.Node(threshold = 0.0, delay=0.0, leak=0.0))

        #OR synapses
        casPYan.connect(nodes[0], nodes[2], weight = 1.0, delay=0.0)
        casPYan.connect(nodes[1], nodes[2], weight = 1.0, delay=0.0)

        inputs = [nodes[0], nodes[1]]
        outputs = [nodes[2]]

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

        expected = [0, 0, 0, 0, 1, 0, 1, 0, 1]

        #Horizontal print
        print("a input   ", processor.inputs[0].history)
        print("b input   ", processor.inputs[1].history)
        print("OR output ", processor.outputs[0].history)

        assert processor.outputs[0].history == expected

if __name__ == "__main__":
    unittest.main()