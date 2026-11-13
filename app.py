"""Run with: streamlit run app.py"""

import csv
from html import escape
import inspect
from io import BytesIO, StringIO
import json
from pathlib import Path
import zipfile

import streamlit as st

from bfs import Node, SearchProblem, bfs, parse_graph
from bfs_simple import bfs_simple
from examples import EXAMPLES
from visuals import graph_html


st.set_page_config(page_title="BFS | Search Lab", page_icon="🔎", layout="wide")

st.markdown("""<style>
.stApp{background:#0b1322;color:#e6edf7}
[data-testid="stSidebar"]{background:#101c2e;border-right:1px solid #24334b}
[data-testid="stSidebar"] .stMarkdown p{color:#afc0d8}
.block-container{padding-top:2rem;max-width:1450px}
.hero{padding:24px 0 28px;border-bottom:1px solid #25334a;margin-bottom:24px}
.eyebrow{color:#55d5e5;letter-spacing:3px;font-size:12px;font-weight:700}
.hero h1{font-size:clamp(30px,4.2vw,58px);letter-spacing:-2px;margin:10px 0;color:#f2f6ff;line-height:1.13}
.hero h1 span{color:#55d5e5}.hero p{color:#9db1ce;font-size:16px;direction:rtl;text-align:left;line-height:1.9}
.chip{display:inline-block;font-size:12px;padding:6px 12px;background:#173049;color:#9ddff1;border:1px solid #2d5166;border-radius:25px;margin:6px 8px 0 0}
.caption{color:#8298b7;font-size:12px;letter-spacing:1.3px;margin:8px 0 15px}
.panel{background:#101c2e;border:1px solid #253650;border-radius:16px;padding:20px;margin-bottom:14px}
.panel h3{font-size:19px;margin:0 0 8px;color:#e6edf7}.panel p{color:#b3c4db;line-height:1.9;margin:0;direction:rtl;text-align:right}
.right{direction:rtl;text-align:right}.right h3{direction:ltr;text-align:left}
.token{display:inline-block;background:#123c55;border:1px solid #38bdf8;color:#c9efff;border-radius:9px;min-width:38px;text-align:center;padding:9px;margin:4px;font-weight:600}
.queue{min-height:76px;direction:ltr}.front{color:#5ed7e6;font-size:12px;direction:ltr}
.small{font-size:13px;color:#94abc8;line-height:1.9}.message{direction:rtl;text-align:right;line-height:1.9;margin-bottom:14px;min-height:65px}
.legend{display:flex;gap:18px;flex-wrap:wrap;direction:rtl;justify-content:center;color:#b1c1d8;font-size:12px;margin:8px 0 20px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-left:6px}
[data-testid="stMetric"]{background:#101c2e;border:1px solid #263851;border-radius:12px;padding:14px}
[data-testid="stMetricValue"]{font-size:27px}
.stTabs [data-baseweb="tab-list"]{gap:25px;border-bottom:1px solid #263650}
.stTabs [data-baseweb="tab"]{font-size:15px;padding-bottom:16px}
.stCode{direction:ltr;text-align:left}button{border-radius:9px!important}
footer{visibility:hidden} .footnote{color:#6f87a7;font-size:12px;padding:25px 0;direction:rtl}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
<div class="eyebrow">SEARCH LAB / BREADTH-FIRST SEARCH</div>
<h1>One level <span>at a time.</span></h1>
<p>صِيغ المسألة، وشوف BFS وهي بتزور الحالات مستوى بمستوى لحد ما توصل للهدف.</p>
<span class="chip">Python + Streamlit</span><span class="chip">FIFO Queue</span><span class="chip">Unit cost = 1</span>
</div>""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### 🔎 BFS / Search Lab")
    st.caption("إعداد المسألة")
    selected = st.selectbox("المثال", [*EXAMPLES, "جراف مخصص · JSON"])
    custom = selected not in EXAMPLES
    example = EXAMPLES[next(iter(EXAMPLES))] if custom else EXAMPLES[selected]
    if custom:
        raw = st.text_area("الجراف · Adjacency list", json.dumps(example["graph"], indent=2), height=270)
        st.caption('الصيغة: {"A": ["B"], "B": []}. كل وصلة موجّهة وتكلفتها 1.')
        try:
            graph = parse_graph(raw)
        except ValueError as error:
            st.error(str(error))
            st.stop()
    else:
        graph = {state: neighbors.copy() for state, neighbors in example["graph"].items()}
        st.caption(example["note"])
        with st.expander("عرض الجراف بصيغة JSON"):
            st.json(graph)
    states = list(graph)
    start_default = example["start"] if example["start"] in graph else states[0]
    goal_default = example["goal"] if example["goal"] in graph else states[-1]
    start = st.selectbox("Initial state · البداية", states, index=states.index(start_default), key=f"start_{selected}")
    goal = st.selectbox("Goal state · الهدف", states, index=states.index(goal_default), key=f"goal_{selected}")
    neighbor_order = st.radio("ترتيب الجيران", ["كما في القوائم", "أبجدي"])
    if neighbor_order == "أبجدي":
        graph = {state: sorted(children) for state, children in graph.items()}
    interval = st.slider("مدة الخطوة بالثواني", 0.3, 2.0, 0.8, 0.1)
    st.divider()
    st.markdown("**BFS — Breadth-First Search**")
    st.caption("كل حالة تدخل الطابور مرة واحدة. أول حالة تدخل هي أول حالة تخرج.")


@st.cache_data(show_spinner=False)
def solve(graph, start, goal):
    return bfs(graph, start, goal)


result = solve(graph, start, goal)
problem = SearchProblem(graph, start, goal)
signature = json.dumps([graph, start, goal], ensure_ascii=False)
if st.session_state.get("problem_signature") != signature:
    st.session_state.problem_signature = signature
    st.session_state.frame = 0
    st.session_state.playing = False

simulation, formulation, complexity, source = st.tabs([
    "▶ المحاكاة", "Problem Formulation", "Time & Space", "كود Python",
])


def trace_csv():
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["step", "current", "added", "queue_front_to_back", "processed", "event"])
    for index, step in enumerate(result.steps):
        writer.writerow([index, step.current or "", " ".join(step.added),
                         " ".join(step.queue), " ".join(step.processed), step.event])
    return buffer.getvalue().encode("utf-8-sig")


with simulation:
    @st.fragment(run_every=interval if st.session_state.playing else None)
    def player():
        last = len(result.steps) - 1
        if st.session_state.playing:
            if st.session_state.frame < last:
                st.session_state.frame += 1
            else:
                st.session_state.playing = False
                st.rerun()

        controls = st.columns([1.3, 1.3, 1, 1, 1.1, 1.1])
        if controls[0].button("▶ تشغيل", disabled=st.session_state.playing, width="stretch"):
            if st.session_state.frame == last:
                st.session_state.frame = 0
            st.session_state.playing = True
            st.rerun()
        if controls[1].button("⏸ إيقاف", disabled=not st.session_state.playing, width="stretch"):
            st.session_state.playing = False
            st.rerun()
        if controls[2].button("← السابقة", disabled=st.session_state.frame == 0 or st.session_state.playing, width="stretch"):
            st.session_state.frame -= 1
            st.rerun()
        if controls[3].button("التالية →", disabled=st.session_state.frame == last or st.session_state.playing, width="stretch"):
            st.session_state.frame += 1
            st.rerun()
        if controls[4].button("للنهاية", disabled=st.session_state.playing, width="stretch"):
            st.session_state.frame = last
            st.rerun()
        if controls[5].button("↺ إعادة", width="stretch"):
            st.session_state.frame = 0
            st.session_state.playing = False
            st.rerun()

        index = st.slider("الخطوة", 0, last, key="frame", disabled=st.session_state.playing)
        step = result.steps[index]
        st.caption(f"STEP {index:02d} / {last:02d}   ·   {len(graph)} STATES   ·   {sum(map(len, graph.values()))} DIRECTED EDGES")
        canvas, details = st.columns([2.1, 1], gap="large")
        with canvas:
            positions = None if custom else example["positions"]
            st.iframe(graph_html(graph, start, goal, step, positions), height=510, alt="BFS directed graph and current path")
            st.markdown('''<div class="legend">
            <span><i class="dot" style="background:#fbbf24"></i>الحالة الحالية ومسارها</span>
            <span><i class="dot" style="background:#38bdf8"></i>في الطابور</span>
            <span><i class="dot" style="background:#8c9fbd"></i>تمت زيارتها</span>
            <span><i class="dot" style="background:#34d399"></i>مسار الحل</span>
            </div>''', unsafe_allow_html=True)
        with details:
            if step.event == "ready":
                message = f"نبدأ من {escape(start)} ونضيفها للطابور. لسه مافيش حالة خرجت للفحص."
            elif step.event == "goal":
                message = f"خرجت {escape(goal)} من الطابور ونجح اختبار الهدف. المسار الأخضر هو الحل."
            elif step.event == "failure":
                message = "الطابور فرغ من غير الوصول للهدف. مافيش مسار من البداية المختارة للهدف داخل الجراف."
            else:
                additions = "، ".join(map(escape, step.added)) or "لا يوجد"
                message = f"نزور {escape(step.current)}، ونضيف جيرانها اللي لسه ما اتشافوش. المضاف: {additions}."
            st.markdown(f'<div class="caption">WHAT HAPPENS NOW</div><div class="message">{message}</div>', unsafe_allow_html=True)
            tokens = "".join(f'<span class="token">{escape(node)}</span>' for node in step.queue)
            st.markdown(f'<div class="panel"><h3>Queue · FIFO</h3><div class="front">FRONT → BACK</div><div class="queue">{tokens or "<span class=small>Empty</span>"}</div><div class="small right">الطابور بعد تنفيذ الخطوة</div></div>', unsafe_allow_html=True)
            st.markdown('<div class="caption">VISIT ORDER</div>', unsafe_allow_html=True)
            st.code(" → ".join(step.processed) or "—", language=None)
            st.markdown('<div class="caption">CURRENT PATH</div>', unsafe_allow_html=True)
            st.code(" → ".join(step.path) or "—", language=None)
            if step.event == "goal":
                st.success(f"طول الحل = {len(step.path)-1} وصلة | Path cost = {len(step.path)-1}")
            elif step.event == "failure":
                st.warning("Goal unreachable")
            else:
                st.caption("المسار الحالي طريق للحالة التي نفحصها؛ يصبح حلًا عند الوصول للهدف.")

        visible = result.steps[:index + 1]
        metrics = st.columns(4)
        metrics[0].metric("الحالة الحالية", step.current or "—")
        metrics[1].metric("حالات تمت زيارتها", len(step.processed))
        metrics[2].metric("حالات تم اكتشافها", len(step.discovered))
        metrics[3].metric("أقصى حجم Queue حتى الآن", max(len(item.queue) for item in visible))

    player()
    with st.expander("جدول الخطوات الكامل"):
        rows = [{"Step": i, "Current": item.current or "—", "Added": ", ".join(item.added) or "—",
                 "Queue (front → back)": ", ".join(item.queue) or "[]", "Event": item.event}
                for i, item in enumerate(result.steps)]
        st.dataframe(rows, hide_index=True, width="stretch")
        st.download_button("تحميل الخطوات CSV", trace_csv(), "bfs_trace.csv", "text/csv")


with formulation:
    st.markdown("### صياغة المسألة قبل البحث")
    st.markdown(f"المطلوب إيجاد مسار من **{start}** إلى **{goal}** عبر الوصلات المسموح بها. تكلفة كل انتقال تساوي **1**.")
    left, right = st.columns(2, gap="large")
    reachable = problem.state_space
    cards = [
        ("01 / State space", f"الحالات التي يمكن الوصول لها من البداية: {', '.join(reachable)}."),
        ("02 / Initial state", f"نبدأ من الحالة {start}."),
        ("03 / Actions", "من أي حالة نختار الانتقال إلى واحد من جيرانها المباشرين حسب اتجاه الوصلات."),
        ("04 / Transition model", "اختيار الحركة «انتقل إلى X» يجعل الحالة الجديدة X، بشرط وجود الوصلة."),
        ("05 / Goal test", f"يتحقق الهدف إذا كانت الحالة الحالية مساوية لـ {goal}."),
        ("06 / Path cost", "تكلفة الخطوة = 1. تكلفة المسار هي مجموع الخطوات، أي عدد الوصلات في المسار."),
    ]
    for i, (title, explanation) in enumerate(cards):
        with left if i % 2 == 0 else right:
            st.markdown(f'<div class="panel right"><h3>{title}</h3><p>{escape(explanation)}</p></div>', unsafe_allow_html=True)
    st.caption("الجراف قد يحتوي حالات منفصلة؛ القائمة أعلاه تعرض الحالات الممكن الوصول لها من البداية فقط.")
    st.divider()
    st.markdown("### جرّب حركة واختبار الهدف")
    col1, col2 = st.columns(2)
    with col1:
        inspected = st.selectbox("اختر الحالة", list(graph))
        actions = problem.actions(inspected)
        st.code(f"actions({inspected!r}) = {actions!r}", language="python")
    with col2:
        if actions:
            action = st.selectbox("الحركة · الانتقال إلى", actions)
            next_state = problem.result(inspected, action)
            st.code(f"result({inspected!r}, {action!r}) = {next_state!r}\nstep_cost = 1\ngoal_test({next_state!r}) = {problem.goal_test(next_state)}", language="python")
        else:
            st.info("الحالة دي مافيهاش حركات للخارج.")
    st.markdown("### State، Node، Path")
    st.markdown("**State** هي الحالة نفسها، مثل اسم المدينة. **Node** يسجّل الحالة ومعاها الأب والحركة وتكلفة المسار والعمق. **Path** هو تسلسل الحالات المتصلة من البداية للحالة الحالية.")
    st.code(inspect.getsource(Node), language="python")
    if result.found:
        chain = []
        node = result.solution_node
        while node:
            chain.append({"State": node.state, "Parent": node.parent.state if node.parent else "—",
                          "Action": node.action or "—", "Path cost": node.path_cost, "Depth": node.depth})
            node = node.parent
        st.dataframe(chain[::-1], hide_index=True, width="stretch")
        st.markdown("**تنفيذ الحل:** " + "، ثم ".join(f"انتقل إلى {state}" for state in result.path[1:]) if len(result.path) > 1 else "**تنفيذ الحل:** البداية هي الهدف؛ لا نحتاج أي انتقال.")
    else:
        st.info("لا يوجد تسلسل لتنفيذ الحل لأن الهدف غير قابل للوصول من البداية.")
    with st.expander("مثالان إضافيان من ملف Problem Formulation"):
        st.markdown("**8-Puzzle:** الحالة ترتيب البلاطات والفراغ. الحركات تحريك الفراغ في اتجاه قانوني، والانتقال يبدّل الفراغ مع البلاطة المجاورة. اختبار الهدف يقارن اللوحة بالترتيب المطلوب، والتكلفة 1 لكل حركة.")
        st.markdown("**Maze:** الحالة موضع اللاعب (صف، عمود). الحركات إلى خلايا مفتوحة مجاورة، والجدران تمنع الانتقال. الهدف الوصول إلى خلية الخروج، والتكلفة 1 لكل حركة. المثالان هنا لتوضيح الصياغة.")


with complexity:
    st.markdown("### Time & Space Complexity")
    st.dataframe([
        {"التحليل": "Graph search — هذا الكود بدون سجل الأنيميشن", "Time": "O(V + E)", "Space": "O(V)"},
        {"التحليل": "Search tree — الصيغة المذكورة في السكشن", "Time": "O(b^d)", "Space": "O(b^d)"},
        {"التحليل": "Search tree — حد محافظ عند فحص الهدف بعد إخراجه", "Time": "O(b^(d+1))", "Space": "O(b^(d+1))"},
    ], hide_index=True, width="stretch")
    st.markdown("**V** عدد الحالات، و**E** عدد الوصلات الموجّهة. كل حالة تدخل وتخرج من الطابور مرة واحدة، وكل قائمة جيران تُفحص مرة واحدة كحد أقصى. الذاكرة الإضافية تشمل Queue وdiscovered وروابط الآباء، ولا تشمل تخزين الجراف.")
    st.markdown("**b** أقصى عدد جيران للحالة، و**d** عمق أقرب هدف. صيغة السكشن تفترض التوقف عند توليد الهدف أو حساب المستويات حتى d. هنا نفحص الهدف عند إخراجه من الطابور؛ بعض حالات المستوى d قد تولّد حالات من d+1 قبل خروج الهدف، لذا الحد المحافظ أعلى بمستوى. هذا لا يغيّر حد O(V + E) للجراف المحدود.")
    st.markdown("**خصائص BFS:** كاملة على جراف محدود مع منع التكرار. وفي فضاء بحث غير محدود تكون كاملة إذا كان التفرع محدودًا والهدف على عمق محدود. تضمن أقل عدد وصلات؛ وهذا يساوي أقل تكلفة هنا لأن كل خطوة تكلفتها 1.")
    st.warning("إذا اختلفت تكاليف الوصلات، لا تضمن BFS أقل تكلفة. النسخة الحالية تفترض تكلفة 1 لكل وصلة.")
    m1, m2, m3 = st.columns(3)
    m1.metric("زمن توليد التتبع · ms", f"{result.trace_time_ms:.3f}")
    m2.metric("أقصى Queue · عدد الحالات", result.peak_queue)
    m3.metric("إجمالي الحالات المكتشفة", result.generated)
    st.caption("الزمن يشمل تنفيذ البحث وإنشاء لقطات الخطوات، ويُقاس مرة لكل إعداد محفوظ في الذاكرة المؤقتة. لا يشمل الرسم أو وقت عرض الأنيميشن، وقد يختلف بين الأجهزة. حجم Queue عدد حالات وليس قياسًا بالبايت.")
    st.markdown("**تكلفة الأنيميشن:** نسخ الطابور وقوائم الاكتشاف والزيارة في كل خطوة يحتاج O(V) وقتًا وذاكرة لكل لقطة. لعدد S من اللقطات، يصبح زمن التطبيق O(V + E + S·V) وذاكرة السجل O(S·V). هنا S ≤ V + 2، لذلك قد يصل السجل إلى O(V²). هذه تكلفة العرض التعليمي، وليست تكلفة BFS الأساسية.")


with source:
    st.markdown("### الكود المرتبط بالواجهة")
    st.markdown("ابدأ بـ `SearchProblem` لفهم صياغة المسألة، ثم النسخة القصيرة `bfs_simple` لفهم الطابور بدون تفاصيل الأنيميشن.")
    st.code(inspect.getsource(SearchProblem), language="python")
    st.code(inspect.getsource(bfs_simple), language="python")
    with st.expander("النسخة المستخدمة في الأنيميشن · تشمل تسجيل الخطوات"):
        st.code(inspect.getsource(bfs), language="python")
    st.download_button("تحميل bfs.py", Path(__file__).with_name("bfs.py").read_bytes(), "bfs.py", "text/x-python")
    st.markdown("**ليه بنسجّل الحالة وقت دخول الطابور؟** عشان ما تدخلش مرتين لو أكتر من طريق وصل لها، وكمان عشان الدورات ما تخلّيش البحث يفضل يعيد نفس الحالات.")
    st.markdown("**ليه ترتيب الزيارة مختلف عن مسار الحل؟** الزيارة تشمل الحالات اللي الخوارزمية فحصتها. الحل بنتتبعه من الهدف للبداية باستخدام `parent` ثم نعكسه.")

st.markdown('<div class="footnote">مبني على الأمثلة الواردة في ملفات السكشن، والمثال المحلول، وProblem Formulation المرفقة. الرسوم تعليمية.</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def project_archive(files):
    """Package source and documentation; exclude caches and local environments."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in files:
            archive.writestr(f"BFS_Search_Lab/{name}", contents)
    return buffer.getvalue()


project_root = Path(__file__).parent
report_path = project_root / "BFS_Problem_Formulation.pdf"
if report_path.exists():
    file_names = ["app.py", "bfs.py", "bfs_simple.py", "examples.py", "visuals.py",
                  "requirements.txt", "README.md", ".streamlit/config.toml",
                  "tests/test_bfs.py", "BFS_Problem_Formulation.pdf"]
    contents = tuple((name, (project_root / name).read_bytes()) for name in file_names)
    with st.sidebar:
        st.divider()
        st.caption("ملفات المشروع والشرح")
        st.download_button("تحميل الشرح PDF", report_path.read_bytes(),
                           report_path.name, "application/pdf", on_click="ignore")
        st.download_button("تحميل المشروع كاملًا ZIP", project_archive(contents),
                           "BFS_Search_Lab.zip", "application/zip", on_click="ignore")
