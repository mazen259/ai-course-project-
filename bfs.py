"""BFS: Queue + visited + parent. Each edge costs 1."""
from collections import deque


def bfs(graph, start, goal):
    queue = deque([start])
    visited = {start}          # Mark a state when it enters the queue.
    parent = {start: None}     # Remember how we reached each state.
    order = []
    steps = []

    while queue:
        current = queue.popleft()
        order.append(current)

        # Follow parent links to build the route to the current state.
        path = []
        node = current
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()

        if current != goal:
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        # Copies keep earlier animation steps unchanged.
        steps.append({
            "current": current,
            "queue": list(queue),
            "order": order.copy(),
            "path": path,
        })

        if current == goal:
            return path, steps

    return [], steps          # No path to the goal.
