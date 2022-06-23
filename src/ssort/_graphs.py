from __future__ import annotations

from typing import AbstractSet, Callable, Generic, Hashable, TypeVar

from ssort._utils import sort_key_from_iter

_N = TypeVar("_N", bound=Hashable)
_E = TypeVar("_E")


class Graph(Generic[_N, _E]):
    def __init__(self) -> None:
        self._out_edges: dict[_N, dict[_N, _E]] = {}
        self._in_edges: dict[_N, dict[_N, _E]] = {}

    @property
    def nodes(self) -> AbstractSet[_N]:
        return self._out_edges.keys()

    def successors(self, node: _N, /) -> AbstractSet[_N]:
        return self._out_edges[node].keys()

    def predecessors(self, node: _N, /) -> AbstractSet[_N]:
        return self._in_edges[node].keys()

    def has_edge(self, origin: _N, destination: _N, /) -> bool:
        out_edges = self._out_edges.get(origin)
        return out_edges is not None and destination in out_edges

    def edge(self, origin: _N, destination: _N, /) -> _E:
        return self._out_edges[origin][destination]

    def add_node(self, node: _N, /) -> None:
        self._out_edges.setdefault(node, {})
        self._in_edges.setdefault(node, {})

    def add_edge(self, origin: _N, destination: _N, edge: _E, /) -> None:
        # Avoid updating state in case of KeyError
        out_edges = self._out_edges[origin]
        in_edges = self._in_edges[destination]

        out_edges[destination] = in_edges[origin] = edge

    def remove_node(self, node: _N, /) -> None:
        # Avoid updating state in case of KeyError. Create copies to properly
        # handle removal of self-referencing nodes.
        out_edges = dict(self._out_edges[node])
        in_edges = dict(self._in_edges[node])

        for destination in out_edges:
            self._in_edges[destination].pop(node, None)  # type: ignore
        for origin in in_edges:
            self._out_edges[origin].pop(node, None)  # type: ignore

        self._out_edges.pop(node)
        self._in_edges.pop(node)

    def remove_edge(self, origin: _N, destination: _N, /) -> None:
        # Avoid updating state in case of KeyError
        out_edges = self._out_edges[origin]
        in_edges = self._in_edges[destination]

        out_edges.pop(destination, None)  # type: ignore
        in_edges.pop(origin, None)  # type: ignore

    def update(self, other: Graph[_N, _E], /) -> None:
        for node in other.nodes:
            self.add_node(node)
            self._out_edges[node].update(other._out_edges[node])
            self._in_edges[node].update(other._in_edges[node])

    def copy(self) -> Graph[_N, _E]:
        copy: Graph[_N, _E] = Graph()
        copy.update(self)
        return copy


def _remove_self_references(graph: Graph[_N, _E]) -> None:
    for node in graph.nodes:
        graph.remove_edge(node, node)


def _find_cycle(graph: Graph[_N, _E]) -> list[_N] | None:
    processed = set()
    for node in graph.nodes:
        if node in processed:
            continue

        in_stack = {node}
        stack = [(node, set(graph.successors(node)))]

        while stack:
            top_node, top_dependencies = stack[-1]

            if not top_dependencies:
                processed.add(top_node)
                in_stack.remove(top_node)
                stack.pop()
                continue

            dependency = top_dependencies.pop()
            if dependency in in_stack:
                cycle = [dependency]
                while stack[-1][0] != dependency:
                    cycle.append(stack[-1][0])
                    stack.pop()
                return cycle
            if dependency not in processed:
                stack.append((dependency, set(graph.successors(dependency))))
                in_stack.add(dependency)

    return None


def replace_cycles(
    graph: Graph[_N, bool], *, key: Callable[[_N], int]
) -> None:
    """
    Finds all cycles and replaces them with forward links that keep them from
    being re-ordered.
    """
    _remove_self_references(graph)
    while True:
        cycle = _find_cycle(graph)
        if not cycle:
            break

        for node in cycle:
            for dependency in cycle:
                graph.remove_edge(node, dependency)

        # TODO this is a bit of an abstraction leak.  Need a better way to tell
        # this function what the safe order is.
        nodes = iter(sorted(cycle, key=key))
        prev = next(nodes)
        for node in nodes:
            graph.add_edge(node, prev, True)
            prev = node


def is_topologically_sorted(nodes: list[_N], graph: Graph[_N, _E]) -> bool:
    visited = set()
    for node in nodes:
        visited.add(node)
        for dependency in graph.successors(node):
            if dependency not in visited:
                return False
    return True


def topological_sort(
    target: Graph[_N, _E] | list[_N], /, *, graph: Graph[_N, _E] | None = None
) -> list[_N]:
    if graph is None:
        if not isinstance(target, Graph):
            raise TypeError("target must be a Graph")
        graph = target
        nodes = list(target.nodes)
    else:
        if not isinstance(target, list):
            raise TypeError("target must be a list")
        nodes = target

    # Create a mutable copy of the graph so that we can pop edges from it as we
    # traverse.
    remaining = graph.copy()

    key = sort_key_from_iter(nodes)

    pending = [node for node in graph.nodes if not graph.predecessors(node)]

    result = []
    while pending:
        pending = list(sorted(pending, key=key))
        node = pending.pop()
        dependencies = remaining.successors(node)
        remaining.remove_node(node)

        for dependency in dependencies:
            if not remaining.predecessors(dependency):
                if dependency not in pending:
                    pending.append(dependency)

        result.append(node)

    result.reverse()

    assert not remaining.nodes
    assert is_topologically_sorted(result, graph)

    return [node for node in result if node in nodes]
