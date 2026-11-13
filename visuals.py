"""Small SVG renderer. No plotting libraries or external services are needed."""

from collections import deque
from html import escape
import math

from bfs import Graph, Step


def auto_positions(graph: Graph, start: str) -> dict:
    """Arrange the reachable states by distance; place disconnected states last."""
    levels = {start: 0}
    pending = deque([start])
    while pending:
        state = pending.popleft()
        for child in graph[state]:
            if child not in levels:
                levels[child] = levels[state] + 1
                pending.append(child)
    last = max(levels.values()) + 1
    for state in graph:
        levels.setdefault(state, last)
    groups = {}
    for state in graph:
        groups.setdefault(levels[state], []).append(state)
    positions = {}
    count = len(groups)
    for row, states in enumerate(groups.values()):
        y = 285 if count == 1 else 70 + row * 430 / (count - 1)
        for column, state in enumerate(states):
            positions[state] = (1000 * (column + 1) / (len(states) + 1), y)
    return positions


def graph_html(graph: Graph, start: str, goal: str, step: Step,
               positions: dict | None = None) -> str:
    positions = positions or auto_positions(graph, start)
    active_edges = set(zip(step.path, step.path[1:]))
    solved = step.event == "goal"
    parts = []
    for source, neighbors in graph.items():
        for target in neighbors:
            x1, y1 = positions[source]
            x2, y2 = positions[target]
            highlighted = (source, target) in active_edges
            color = "#34d399" if highlighted and solved else "#fbbf24" if highlighted else "#3c526d"
            width = 4 if highlighted else 2
            if source == target:
                route = f"M {x1-20} {y1-22} C {x1-80} {y1-110}, {x1+80} {y1-110}, {x1+24} {y1-22}"
            else:
                dx, dy = x2 - x1, y2 - y1
                length = math.hypot(dx, dy)
                ux, uy = dx / length, dy / length
                a, b = x1 + ux * 34, y1 + uy * 34
                c, d = x2 - ux * 42, y2 - uy * 42
                bend = 22 if source in graph[target] else 0
                mx, my = (a+c)/2 - uy*bend, (b+d)/2 + ux*bend
                route = f"M {a} {b} Q {mx} {my} {c} {d}"
            marker = "green" if highlighted and solved else "gold" if highlighted else "base"
            parts.append(f'<path d="{route}" fill="none" stroke="{color}" stroke-width="{width}" marker-end="url(#{marker})"/>')

    for state, (x, y) in positions.items():
        label = escape(state)
        if solved and state in step.path:
            fill, stroke = "#073f39", "#34d399"
        elif state == step.current:
            fill, stroke = "#573e12", "#fbbf24"
        elif state in step.queue:
            fill, stroke = "#113d58", "#38bdf8"
        elif state in step.processed:
            fill, stroke = "#263653", "#8c9fbd"
        else:
            fill, stroke = "#142137", "#4a5e7b"
        if state == step.current:
            parts.append(f'<circle cx="{x}" cy="{y}" r="42" fill="none" stroke="{stroke}" opacity="0.4" class="pulse"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="32" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
        font_size = 18 if len(state) < 5 else 12 if len(state) < 10 else 10
        parts.append(f'<text x="{x}" y="{y+6}" text-anchor="middle" fill="#edf5ff" font-size="{font_size}" font-weight="600">{label}</text>')
        badge = "START / GOAL" if state == start == goal else "START" if state == start else "GOAL" if state == goal else ""
        if badge:
            parts.append(f'<text x="{x}" y="{y+58}" text-anchor="middle" fill="#9bb2cf" font-size="11" letter-spacing="1.5">{badge}</text>')
        if state in step.processed:
            order = step.processed.index(state) + 1
            parts.append(f'<circle cx="{x+26}" cy="{y-25}" r="12" fill="#253b56" stroke="#9bb2cf"/><text x="{x+26}" y="{y-21}" text-anchor="middle" fill="white" font-size="11">{order}</text>')

    return '''<!doctype html><html><head><meta charset="utf-8"><style>
    body{margin:0;background:#101c2e;font-family:Arial,sans-serif}
    svg{width:100%;height:100%;max-height:540px} .pulse{animation:pulse 1.2s infinite}
    @keyframes pulse{50%{opacity:.12;stroke-width:6}}
    @media(prefers-reduced-motion:reduce){.pulse{animation:none}}
    </style></head><body><svg viewBox="0 0 1000 580" role="img" aria-label="Directed graph and current BFS step">
    <defs>''' + "".join(
        f'<marker id="{name}" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M 0 0 L 8 4 L 0 8 z" fill="{color}"/></marker>'
        for name, color in [("base", "#3c526d"), ("gold", "#fbbf24"), ("green", "#34d399")]
    ) + "</defs>" + "".join(parts) + "</svg></body></html>"
