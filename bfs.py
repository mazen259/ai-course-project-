"""Breadth-first graph search, independent of the Streamlit interface.

All edges cost one. Neighbors are considered in the supplied list order.
"""

from collections import deque
from dataclasses import dataclass
import json
from time import perf_counter


Graph = dict[str, list[str]]


@dataclass
class SearchProblem:
    """The six formulation components for a unit-cost directed graph."""

    graph: Graph
    initial_state: str
    goal_state: str

    def __post_init__(self):
        validate_graph(self.graph)
        if self.initial_state not in self.graph or self.goal_state not in self.graph:
            raise ValueError("البداية والهدف لازم يكونوا موجودين في الجراف.")

    @property
    def state_space(self) -> list[str]:
        return reachable_states(self.graph, self.initial_state)

    def actions(self, state: str) -> list[str]:
        # An action is named by its destination, e.g. action "C" = move to C.
        return self.graph[state]

    def result(self, state: str, action: str) -> str:
        # Precondition: action was selected from actions(state).
        return action

    def goal_test(self, state: str) -> bool:
        return state == self.goal_state

    def step_cost(self, state: str, action: str) -> int:
        return 1


@dataclass(frozen=True)
class Node:
    """A search node = a state plus the path used to reach that state."""

    state: str
    parent: "Node | None" = None
    action: str | None = None
    path_cost: int = 0
    depth: int = 0


@dataclass(frozen=True)
class Step:
    current: str | None
    added: tuple[str, ...]
    queue: tuple[str, ...]  # front -> back, after this step
    discovered: tuple[str, ...]
    processed: tuple[str, ...]
    path: tuple[str, ...]   # route to the current node
    event: str             # ready, expand, goal, or failure
    depth: int = 0


@dataclass
class SearchResult:
    found: bool
    path: list[str]
    order: list[str]
    steps: list[Step]
    peak_queue: int
    generated: int
    trace_time_ms: float
    solution_node: Node | None


def build_path(node: Node | None) -> list[str]:
    """Follow parent links backward, then reverse to get start -> current."""
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return path[::-1]


def validate_graph(graph: Graph) -> None:
    if not isinstance(graph, dict) or not graph:
        raise ValueError("الجراف لازم يكون قاموسًا غير فارغ.")
    if len(graph) > 30:
        raise ValueError("استخدم 30 حالة بحد أقصى لتظل الرسمة واضحة.")
    edge_count = 0
    for state, neighbors in graph.items():
        if not isinstance(state, str) or not state.strip() or len(state) > 14:
            raise ValueError("اسم الحالة نص غير فارغ بطول 14 حرفًا بحد أقصى.")
        if not isinstance(neighbors, list):
            raise ValueError("جيران كل حالة لازم يكونوا داخل قائمة JSON.")
        if any(not isinstance(child, str) for child in neighbors):
            raise ValueError("أسماء الجيران لازم تكون نصوصًا.")
        if len(neighbors) != len(set(neighbors)):
            raise ValueError("احذف الجيران المكررين من القائمة نفسها.")
        if any(child not in graph for child in neighbors):
            raise ValueError("كل جار لازم يكون له مفتاح في الجراف، حتى لو قائمته فارغة.")
        edge_count += len(neighbors)
    if edge_count > 120:
        raise ValueError("استخدم 120 وصلة بحد أقصى.")


def parse_graph(text: str) -> Graph:
    """Read adjacency-list JSON; reject duplicate keys instead of losing data."""
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"المفتاح {key!r} مكرر في JSON.")
            result[key] = value
        return result

    try:
        graph = json.loads(text, object_pairs_hook=unique_keys)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON غير صالح عند السطر {error.lineno}.") from error
    validate_graph(graph)
    return graph


def bfs(graph: Graph, start: str, goal: str) -> SearchResult:
    """Find a path with the fewest edges and record the queue for animation.

    Mark states when enqueued, so cycles cannot enqueue a state twice.
    Check the goal when dequeued, matching the supplied worked example.
    """
    problem = SearchProblem(graph, start, goal)

    started = perf_counter()
    root = Node(start)
    queue = deque([root])
    discovered = {start}
    discovery_order = [start]
    processed = []
    steps = []
    peak_queue = 1

    def record(current, added, event):
        steps.append(Step(
            current=current.state if current else None,
            added=tuple(added),
            queue=tuple(node.state for node in queue),
            discovered=tuple(discovery_order),
            processed=tuple(processed),
            path=tuple(build_path(current)),
            event=event,
            depth=current.depth if current else 0,
        ))

    def finish(solution):
        return SearchResult(
            found=solution is not None,
            path=build_path(solution),
            order=processed.copy(),
            steps=steps,
            peak_queue=peak_queue,
            generated=len(discovered),
            trace_time_ms=(perf_counter() - started) * 1000,
            solution_node=solution,
        )

    record(None, [start], "ready")
    while queue:
        current = queue.popleft()  # FIFO: remove the oldest search node.
        processed.append(current.state)

        if problem.goal_test(current.state):
            record(current, [], "goal")
            return finish(current)

        added = []
        for action in problem.actions(current.state):
            neighbor = problem.result(current.state, action)
            if neighbor not in discovered:
                discovered.add(neighbor)  # Mark BEFORE enqueueing.
                discovery_order.append(neighbor)
                child = Node(
                    state=neighbor,
                    parent=current,
                    action=f"Move to {neighbor}",
                    path_cost=current.path_cost + problem.step_cost(current.state, action),
                    depth=current.depth + 1,
                )
                queue.append(child)
                added.append(neighbor)

        peak_queue = max(peak_queue, len(queue))
        record(current, added, "expand")

    record(None, [], "failure")
    return finish(None)


def reachable_states(graph: Graph, start: str) -> list[str]:
    """Reachable state space for the problem-formulation panel."""
    reached = {start}
    pending = deque([start])
    while pending:
        state = pending.popleft()
        for child in graph[state]:
            if child not in reached:
                reached.add(child)
                pending.append(child)
    return [state for state in graph if state in reached]


if __name__ == "__main__":
    graph = {
        "A": ["B", "C"], "B": [], "C": ["B", "E", "F"],
        "D": ["B", "E", "G"], "E": ["G"], "F": ["D", "H"],
        "G": ["H"], "H": [],
    }
    result = bfs(graph, "A", "H")
    print("Visit order:", " -> ".join(result.order))
    print("Solution:", " -> ".join(result.path))
    print("Path cost:", result.solution_node.path_cost if result.found else None)
