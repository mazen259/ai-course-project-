"""Run: python -m streamlit run app.py"""
import time
import streamlit as st
from bfs import bfs

graph = {
    "A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"],
    "D": [], "E": [], "F": [], "G": [],
}

st.set_page_config(page_title="BFS", page_icon="🔎", layout="wide")
st.title("BFS — Breadth-First Search")
st.write("بحث مستوى بمستوى باستخدام Queue: أول حالة تدخل هي أول حالة تخرج.")
start = st.sidebar.selectbox("البداية", list(graph), index=0)
goal = st.sidebar.selectbox("الهدف", list(graph), index=6)
delay = st.sidebar.slider("مدة الخطوة بالثواني", 0.2, 1.5, 0.7)
path, steps = bfs(graph, start, goal)

st.subheader("Problem Formulation")
st.markdown(f"""
- **State space:** الحالات الموجودة في الجراف: {', '.join(graph)}.
- **Initial state:** البداية هي {start}.
- **Actions:** الانتقال إلى جار مباشر في اتجاه السهم.
- **Transition model:** اختيار جار يجعل هذا الجار هو الحالة الجديدة.
- **Goal test:** هل الحالة الحالية تساوي {goal}؟
- **Path cost:** تكلفة كل وصلة 1؛ تكلفة المسار هي عدد وصلاته.
""")

st.subheader("المحاكاة")
frame = st.slider("الخطوة", 1, len(steps), 1) if len(steps) > 1 else 1
play = st.button("▶ تشغيل الأنيميشن")
screen = st.empty()


def show_step(step):
    """Draw one recorded step. This function does not perform the search."""
    solved = step["current"] == goal
    dot = 'digraph G { rankdir=TB; ordering=out; node [shape=circle, style=filled]; edge [arrowhead=none, color=gray];'
    for node in graph:
        color = "#0f766e" if node != goal else "#111827"
        if node in step["order"]:
            color = "lightgray"
        if node in step["queue"]:
            color = "lightskyblue"
        if node == step["current"]:
            color = "gold"
        if solved and node in step["path"]:
            color = "lightgreen"
        font = "white" if color.startswith("#") else "black"
        number = step["order"].index(node) + 1 if node in step["order"] else ""
        dot += f'{node} [fillcolor="{color}", fontcolor="{font}", xlabel="{number}"];'
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            dot += f'{node} -> {neighbor};'
    dot += '}'

    with screen.container():
        st.graphviz_chart(dot)
        st.caption("أصفر: الحالية | أزرق: في الطابور | رمادي: تمت زيارتها | أخضر: الحل")
        st.write("الحالة الحالية:", step["current"])
        st.code("Queue (front → back): " + str(step["queue"]))
        st.code("Visit order: " + " → ".join(step["order"]))
        st.code("Current path: " + " → ".join(step["path"]))
        if solved:
            st.success(f"الحل: {' → '.join(path)} | التكلفة: {len(path) - 1}")
        elif step == steps[-1] and not path:
            st.warning("لا يوجد مسار من البداية إلى الهدف.")


if play:
    for step in steps:
        show_step(step)
        time.sleep(delay)
else:
    show_step(steps[frame - 1])

st.subheader("Time & Space")
st.code("Time Complexity:  O(b^d)\nSpace Complexity: O(b^d)")
st.write("حسب تحليل شجرة البحث في السكشن: b هو عدد الفروع، وd هو عمق أقرب هدف.")
st.caption("في المثال: b = 2 وd = 2. الجيران من اليسار إلى اليمين. هذه حدود نظرية وليست عدد الحالات التي تمت زيارتها.")
st.caption("الحدود تخص البحث في شجرة الحالات؛ حفظ لقطات الأنيميشن والمسارات يضيف تكلفة عرض مستقلة.")
st.info("BFS تضمن أقل عدد وصلات. مع تكلفة 1 لكل وصلة، يكون الحل أقل تكلفة أيضًا.")
