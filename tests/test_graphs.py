import random

from ssort._graphs import Graph, topological_sort


def test_graph_add_node():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)

    assert graph.nodes == {1, 2}


def test_graph_add_edge():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_edge(1, 2, True)

    assert graph.successors(1) == {2}
    assert graph.predecessors(2) == {1}
    assert graph.edge(1, 2) is True


def test_graph_remove_node():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_edge(1, 2, True)
    graph.remove_node(1)

    assert graph.nodes == {2}
    assert graph.predecessors(2) == set()


def test_graph_remove_edge():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_edge(1, 2, True)
    graph.remove_edge(1, 2)

    assert graph.successors(1) == set()
    assert graph.predecessors(2) == set()
    assert not graph.has_edge(1, 2)


def test_graph_update():
    graph1 = Graph()

    graph1.add_node(1)
    graph1.add_node(2)
    graph1.add_node(3)
    graph1.add_edge(1, 2, 1)
    graph1.add_edge(2, 3, 1)

    graph2 = Graph()

    graph2.add_node(2)
    graph2.add_node(3)
    graph2.add_node(4)
    graph2.add_edge(2, 3, 2)
    graph2.add_edge(3, 4, 2)

    graph1.update(graph2)

    assert graph1.nodes == {1, 2, 3, 4}
    assert graph1.successors(1) == {2}
    assert graph1.successors(2) == {3}
    assert graph1.successors(3) == {4}
    assert graph1.predecessors(2) == {1}
    assert graph1.predecessors(3) == {2}
    assert graph1.predecessors(4) == {3}
    assert graph1.edge(1, 2) == 1
    assert graph1.edge(2, 3) == 2
    assert graph1.edge(3, 4) == 2


def test_topological_sort_chain():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_node(3)
    graph.add_node(4)

    graph.add_edge(2, 1, True)
    graph.add_edge(3, 2, True)
    graph.add_edge(4, 3, True)

    assert topological_sort(graph) == [1, 2, 3, 4]


def test_topological_sort_reversed_chain():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_node(3)
    graph.add_node(4)

    graph.add_edge(1, 2, True)
    graph.add_edge(2, 3, True)
    graph.add_edge(3, 4, True)

    assert topological_sort(graph) == [4, 3, 2, 1]


def test_topological_sort_root():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_node(3)
    graph.add_node(4)

    graph.add_edge(1, 4, True)
    graph.add_edge(2, 4, True)
    graph.add_edge(3, 4, True)

    assert topological_sort(graph) == [4, 1, 2, 3]


def test_topological_sort_tree():
    graph = Graph()

    graph.add_node(1)
    graph.add_node(2)
    graph.add_node(3)
    graph.add_node(4)
    graph.add_node(5)

    graph.add_edge(3, 2, True)
    graph.add_edge(5, 4, True)
    graph.add_edge(5, 3, True)

    assert topological_sort(graph) == [1, 2, 3, 4, 5]


def test_unconnected_stable():
    nodes = list(range(1, 100))
    random.shuffle(nodes)

    graph = Graph()
    for node in nodes:
        graph.add_node(node)

    assert topological_sort(graph) == nodes


def test_random_stable():
    nodes = list(range(100))
    random.shuffle(nodes)

    graph = Graph()

    for node in nodes:
        graph.add_node(node)

    for _ in range(200):
        src_index = random.randrange(1, 100)
        tgt_index = random.randrange(src_index)
        graph.add_edge(nodes[src_index], nodes[tgt_index], True)

    assert topological_sort(graph) == nodes
