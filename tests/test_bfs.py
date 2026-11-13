"""Regression examples from the PDFs plus graph-search edge cases."""

import random

import pytest

from bfs import SearchProblem, bfs, parse_graph
from bfs_simple import bfs_simple
from examples import EXAMPLES


def test_solved_pdf_exact_order_path_and_queue():
    example = EXAMPLES["الجراف المحلول · A → H"]
    result = bfs(example["graph"], "A", "H")
    assert result.order == list("ABCEFGDH")
    assert result.path == ["A", "C", "F", "H"]
    assert result.solution_node.path_cost == 3
    assert result.peak_queue == 3
    assert [list(step.queue) for step in result.steps[1:]] == [
        ["B", "C"], ["C"], ["E", "F"], ["F", "G"],
        ["G", "D", "H"], ["D", "H"], ["H"], [],
    ]


def test_section_tree():
    example = EXAMPLES["شجرة السكشن · A → G"]
    result = bfs(example["graph"], "A", "G")
    assert result.order == list("ABCDEFG")
    assert result.path == ["A", "C", "G"]


def test_formulation_and_city_example():
    graph = EXAMPLES["صياغة المسألة · المدن"]["graph"]
    problem = SearchProblem(graph, "Cairo", "Alexandria")
    assert problem.state_space == list(graph)
    assert problem.actions("Cairo") == ["Giza", "Fayoum"]
    assert problem.result("Cairo", "Giza") == "Giza"
    assert problem.goal_test("Alexandria")
    assert not problem.goal_test("Giza")
    assert problem.step_cost("Cairo", "Giza") == 1
    result = bfs(graph, "Cairo", "Alexandria")
    assert result.path == ["Cairo", "Giza", "Alexandria"]
    assert result.solution_node.path_cost == 2


def test_start_is_goal():
    result = bfs({"A": ["B"], "B": []}, "A", "A")
    assert result.found
    assert result.path == ["A"]
    assert result.order == ["A"]
    assert result.generated == 1
    assert result.solution_node.path_cost == 0


def test_cycles_self_loops_and_unreachable_goal():
    graph = {"A": ["A", "B"], "B": ["A"], "Z": []}
    result = bfs(graph, "A", "Z")
    assert not result.found
    assert result.path == []
    assert result.order == ["A", "B"]
    assert result.steps[-1].event == "failure"
    assert SearchProblem(graph, "A", "Z").state_space == ["A", "B"]


def test_discovered_on_enqueue_keeps_first_parent():
    graph = {"S": ["A", "B"], "A": ["C"], "B": ["C"], "C": ["G"], "G": []}
    result = bfs(graph, "S", "G")
    assert result.path == ["S", "A", "C", "G"]
    assert result.generated == 5
    assert len(result.order) == len(set(result.order))


def test_neighbor_order_changes_equal_length_solution():
    graph = {"S": ["B", "A"], "A": ["G"], "B": ["G"], "G": []}
    assert bfs(graph, "S", "G").path == ["S", "B", "G"]


@pytest.mark.parametrize("text", [
    "{}", "[]", '{"A": ["B"]}', '{"A": [1]}',
    '{"A": ["A", "A"]}', '{"A": [], "A": []}',
    '{"A": 4}', '{"A": []', '{"": []}',
])
def test_invalid_graphs_rejected(text):
    with pytest.raises(ValueError):
        parse_graph(text)


def test_valid_json_and_missing_start():
    assert parse_graph('{"A": ["B"], "B": []}') == {"A": ["B"], "B": []}
    with pytest.raises(ValueError):
        bfs({"A": []}, "missing", "A")


def test_shortest_paths_against_independent_distance_relaxation():
    rng = random.Random(17)
    for _ in range(80):
        states = list("ABCDEFG")
        graph = {a: [b for b in states if rng.random() < 0.22] for a in states}
        # Repeated edge relaxation computes distances without using a queue.
        distance = {state: float("inf") for state in states}
        distance["A"] = 0
        for _ in range(len(states) - 1):
            for source, children in graph.items():
                for target in children:
                    distance[target] = min(distance[target], distance[source] + 1)
        result = bfs(graph, "A", "G")
        assert result.found == (distance["G"] < float("inf"))
        if result.found:
            assert len(result.path) - 1 == distance["G"]
            assert all(b in graph[a] for a, b in zip(result.path, result.path[1:]))
        for step in result.steps:
            assert len(step.queue) == len(set(step.queue))
            assert set(step.queue).isdisjoint(step.processed)
            assert set(step.queue) | set(step.processed) == set(step.discovered)


def test_graph_limits():
    with pytest.raises(ValueError):
        bfs({str(i): [] for i in range(31)}, "0", "1")
    states = [str(i) for i in range(12)]
    with pytest.raises(ValueError):
        bfs({state: states.copy() for state in states}, "0", "1")


def test_simple_version_matches_animated_search():
    for example in EXAMPLES.values():
        problem = SearchProblem(example["graph"], example["start"], example["goal"])
        path, order = bfs_simple(problem)
        result = bfs(problem.graph, problem.initial_state, problem.goal_state)
        assert path == result.path
        assert order == result.order
