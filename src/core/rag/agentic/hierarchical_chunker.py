import re
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class HierarchicalChunk:
    id: str
    text: str
    metadata: dict
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    level: str = "child"

    @property
    def is_parent(self) -> bool:
        return self.level == "parent"

    @property
    def is_child(self) -> bool:
        return self.level == "child"


class HierarchicalChunker:
    HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)$", re.MULTILINE)

    def __init__(
        self,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 500,
        child_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap
        self.min_chunk_size = min_chunk_size

    def chunk(
        self,
        text: str,
        source: str = "unknown",
    ) -> Tuple[List[HierarchicalChunk], List[HierarchicalChunk]]:
        parents = self._create_parent_chunks(text, source)
        children = []

        for parent in parents:
            parent_children = self._split_to_children(parent)
            children.extend(parent_children)

        return parents, children

    def chunk_flat(
        self,
        text: str,
        source: str = "unknown",
    ) -> List[HierarchicalChunk]:
        parents, children = self.chunk(text, source)
        return parents + children

    def _create_parent_chunks(
        self,
        text: str,
        source: str,
    ) -> List[HierarchicalChunk]:
        headers = list(self.HEADER_RE.finditer(text))

        if not headers:
            return self._chunk_by_size(text, source, "parent")

        chunks = []
        header_stack: List[str] = []

        for i, match in enumerate(headers):
            level = len(match.group(1))
            title = match.group(2).strip()

            start = match.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)

            section_text = text[start:end].strip()

            while len(header_stack) >= level:
                header_stack.pop()
            header_stack.append(title)

            if len(section_text) < self.min_chunk_size:
                continue

            if len(section_text) > self.parent_chunk_size:
                sub_chunks = self._chunk_by_size(
                    section_text, source, "parent", base_headers=list(header_stack)
                )
                chunks.extend(sub_chunks)
            else:
                chunk_id = self._generate_id(source, i, "parent")
                chunks.append(
                    HierarchicalChunk(
                        id=chunk_id,
                        text=section_text,
                        metadata={
                            "source": source,
                            "headers": list(header_stack),
                            "level": level,
                        },
                        level="parent",
                    )
                )

        return chunks

    def _chunk_by_size(
        self,
        text: str,
        source: str,
        level: str,
        base_headers: Optional[List[str]] = None,
    ) -> List[HierarchicalChunk]:
        chunks = []
        target_size = (
            self.parent_chunk_size if level == "parent" else self.child_chunk_size
        )

        paragraphs = re.split(r"\n\n+", text)
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= target_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunk_id = self._generate_id(source, chunk_idx, level)
                    chunks.append(
                        HierarchicalChunk(
                            id=chunk_id,
                            text=current_chunk,
                            metadata={
                                "source": source,
                                "headers": base_headers or [],
                                "chunk_index": chunk_idx,
                            },
                            level=level,
                        )
                    )
                    chunk_idx += 1

                current_chunk = para

        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunk_id = self._generate_id(source, chunk_idx, level)
            chunks.append(
                HierarchicalChunk(
                    id=chunk_id,
                    text=current_chunk,
                    metadata={
                        "source": source,
                        "headers": base_headers or [],
                        "chunk_index": chunk_idx,
                    },
                    level=level,
                )
            )

        return chunks

    def _split_to_children(
        self,
        parent: HierarchicalChunk,
    ) -> List[HierarchicalChunk]:
        text = parent.text
        children = []

        if len(text) <= self.child_chunk_size:
            return []

        start = 0
        idx = 0
        max_iterations = (
            len(text) // max(1, self.child_chunk_size - self.child_overlap) + 10
        )

        iteration = 0
        while start < len(text) and iteration < max_iterations:
            iteration += 1
            end = min(start + self.child_chunk_size, len(text))

            if end < len(text):
                break_point = self._find_break_point(text, start, end)
                if break_point > start:
                    end = break_point

            child_text = text[start:end].strip()

            if len(child_text) >= self.min_chunk_size:
                child_id = f"{parent.id}::child_{idx}"
                child = HierarchicalChunk(
                    id=child_id,
                    text=child_text,
                    metadata={
                        **parent.metadata,
                        "parent_id": parent.id,
                        "child_index": idx,
                    },
                    parent_id=parent.id,
                    level="child",
                )
                children.append(child)
                parent.children_ids.append(child_id)
                idx += 1

            next_start = end - self.child_overlap
            if next_start <= start:
                next_start = end

            if next_start >= len(text):
                break

            start = next_start

        return children

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        search_text = text[start:end]

        for delimiter in ["\n\n", "\n", ". ", ", ", " "]:
            last_pos = search_text.rfind(delimiter)
            if last_pos > len(search_text) // 2:
                return start + last_pos + len(delimiter)

        return end

    def _generate_id(self, source: str, index: int, level: str) -> str:
        short_uuid = str(uuid.uuid4())[:8]
        safe_source = re.sub(r"[^a-zA-Z0-9]", "_", source)[:20]
        return f"{safe_source}::{level}_{index}_{short_uuid}"

    def get_parent_for_child(
        self,
        child: HierarchicalChunk,
        parents: List[HierarchicalChunk],
    ) -> Optional[HierarchicalChunk]:
        if not child.parent_id:
            return None

        for parent in parents:
            if parent.id == child.parent_id:
                return parent

        return None
