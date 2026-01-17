import re 
from pathlib import Path
from typing import List


HEADER_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$",
re.MULTILINE)
def make_knowledge_text(files) -> str:
    entire_knowlegde_base = ""
    with open(files, "r", encoding="utf-8") as f:
        entire_knowlegde_base += f.read()
        entire_knowlegde_base += "\n\n"
        
    return entire_knowlegde_base
base = Path.cwd() / "src/test/Transformer models.md"
knowledge_text = make_knowledge_text(str(base))


def extract_header_marks(texts: str | List[str]) -> List[tuple[int, List[str]]]:
    """
    문서를 위에서 아래로 읽으면서, \n
    “현재 내가 속한 #/##/### 섹션 경로”를 계속 업데이트하고, \n
    헤더가 등장하는 위치마다 (그 위치, 그때의 경로)를 기록하는 함수 \n
    """
    header_marks = []
    stack = [None, None, None]  # levels 1..3

    for m in HEADER_RE.finditer(text):
        level = len(m.group(1))
        title = m.group(2).strip()

        stack[level-1] = title
        for i in range(level, 3): stack[i] = None
        path = [x for x in stack if x]
        header_marks.append((m.start(), path))
    return header_marks
extract_header_marks(knowledge_text)

