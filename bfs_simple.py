"""Start here to understand BFS without animation bookkeeping.

Run: python bfs_simple.py
"""
from collections import deque

from bfs import Node, SearchProblem, build_path


def bfs_simple(problem: SearchProblem):
    queue = deque([Node(problem.initial_state)])
    discovered = {problem.initial_state}
    visit_order = []

    while queue:
        current = queue.popleft()
        visit_order.append(current.state)

        if problem.goal_test(current.state):
            return build_path(current), visit_order

        for action in problem.actions(current.state):
            next_state = problem.result(current.state, action)
            if next_state not in discovered:
                discovered.add(next_state)
                child = Node(
                    state=next_state,
                    parent=current,
                    action=f"Move to {next_state}",
                    path_cost=current.path_cost + 1,
                    depth=current.depth + 1,
                )
                queue.append(child)

    return [], visit_order


if __name__ == "__main__":
    from examples import EXAMPLES

    example = next(iter(EXAMPLES.values()))
    problem = SearchProblem(example["graph"], example["start"], example["goal"])
    path, order = bfs_simple(problem)
    print("Visit order:", " -> ".join(order))
    print("Solution:", " -> ".join(path))
    print("Path cost:", len(path) - 1 if path else "No solution")
