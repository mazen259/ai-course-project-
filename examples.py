"""Examples transcribed from the user's three reference PDFs."""

EXAMPLES = {
    "الجراف المحلول · A → H": {
        "graph": {
            "A": ["B", "C"], "B": [], "C": ["B", "E", "F"],
            "D": ["B", "E", "G"], "E": ["G"], "F": ["D", "H"],
            "G": ["H"], "H": [],
        },
        "start": "A", "goal": "H",
        "note": "من BFS_DFS_Solved_Problem.pdf. البداية A والهدف H وفق افتراضات الحل، والوصلة F → D.",
        "positions": {"A": (100, 240), "B": (300, 100), "C": (300, 350),
                      "E": (500, 330), "F": (620, 490), "D": (500, 100),
                      "G": (700, 240), "H": (900, 370)},
    },
    "شجرة السكشن · A → G": {
        "graph": {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"],
                  "D": [], "E": [], "F": [], "G": []},
        "start": "A", "goal": "G",
        "note": "من BFS&DFS section.pdf. ترتيب الجيران من اليسار إلى اليمين.",
        "positions": {"A": (500, 90), "B": (270, 260), "C": (730, 260),
                      "D": (140, 460), "E": (380, 460),
                      "F": (620, 460), "G": (860, 460)},
    },
    "صياغة المسألة · المدن": {
        "graph": {"Cairo": ["Giza", "Fayoum"], "Giza": ["Cairo", "Alexandria"],
                  "Fayoum": ["Cairo"], "Alexandria": ["Giza"]},
        "start": "Cairo", "goal": "Alexandria",
        "note": "من Problem_Formulation.pdf. كل انتقال تكلفته 1؛ الرسم تعليمي ولا يمثل المسافات الجغرافية.",
        "positions": {"Cairo": (260, 180), "Giza": (630, 180),
                      "Fayoum": (260, 440), "Alexandria": (630, 440)},
    },
}
