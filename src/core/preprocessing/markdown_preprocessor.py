"""
Markdown Preprocessor for RAG

헤더 기반 Semantic Chunking을 수행하는 전처리 모듈.
- YAML frontmatter 추출
- 코드 블록 보호
- 헤더 계층 구조 추적
- 청크 크기 제어 (병합/분할)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ============================================================================
# Constants
# ============================================================================

MIN_CHUNK_SIZE = 200  # 이 길이보다 짧으면 다음 섹션과 병합
MAX_CHUNK_SIZE = 1500  # 이 길이보다 길면 문단 단위로 분할

# 정규표현식 패턴
HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
#                        ↑ Group 1  ↑ Group 2
#                        (# 기호들)    (제목 텍스트)
YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n?---\s*\n", re.DOTALL)
CODE_BLOCK_RE = re.compile(r"(```+)([^\n]*)\n(.*?)\1", re.DOTALL)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class YAMLFrontmatter:
    """YAML frontmatter 데이터"""

    raw: str
    tags: List[str] = field(default_factory=list) 
    create_date: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def parse(cls, raw: str) -> "YAMLFrontmatter":
        """YAML 문자열을 파싱하여 YAMLFrontmatter 객체 생성"""
        tags: List[str] = []
        create_date: Optional[str] = None
        extra: dict = {}

        for line in raw.strip().split("\n"):
            line = line.strip()
            if line.startswith("- "):
                # 태그 리스트 항목
                tags.append(line[2:].strip())
            elif ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key == "create":
                    create_date = value
                elif key != "tags":
                    extra[key] = value

        return cls(raw=raw, tags=tags, create_date=create_date, extra=extra)


@dataclass
class HeaderMark:
    """헤더 위치 및 계층 정보"""

    position: int  # 문서 내 시작 위치
    end_position: int  # 헤더 라인 끝 위치
    level: int  # 헤더 레벨 (1-6)
    title: str  # 헤더 제목
    path: List[str]  # 상위 헤더 포함 경로 (breadcrumb)


@dataclass
class Chunk:
    """RAG용 청크 데이터"""

    text: str
    metadata: dict


# ============================================================================
# Code Block Protection
# ============================================================================


def protect_code_blocks(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    코드 블록을 플레이스홀더로 치환하여 청킹 시 분할되지 않도록 보호.

    Returns:
        (치환된 텍스트, [(플레이스홀더, 원본 코드블록), ...])
    """
    placeholders: List[Tuple[str, str]] = []

    def replacer(match: re.Match) -> str:
        placeholder = f"__CODE_BLOCK_{len(placeholders)}__"
        placeholders.append((placeholder, match.group(0)))
        return placeholder

    protected_text = CODE_BLOCK_RE.sub(replacer, text)
    return protected_text, placeholders


def restore_code_blocks(text: str, placeholders: List[Tuple[str, str]]) -> str:
    """플레이스홀더를 원본 코드 블록으로 복원"""
    for placeholder, original in placeholders:
        text = text.replace(placeholder, original)
    return text


# ============================================================================
# YAML Frontmatter Extraction
# ============================================================================


def extract_frontmatter(text: str) -> Tuple[Optional[YAMLFrontmatter], str]:
    """
    YAML frontmatter를 추출하고 본문에서 제거.

    Returns:
        (YAMLFrontmatter 객체 또는 None, frontmatter 제거된 본문)
    """
    match = YAML_FRONTMATTER_RE.match(text)
    if match:
        yaml_content = match.group(1)
        body = text[match.end() :]
        return YAMLFrontmatter.parse(yaml_content), body
    return None, text


# ============================================================================
# Header Extraction
# ============================================================================


def extract_header_marks(text: str) -> List[HeaderMark]:
    """
    문서에서 모든 헤더를 추출하고 계층 구조를 추적.

    각 헤더에 대해:
    - 문서 내 위치
    - 헤더 레벨 (1-6)
    - 제목
    - 상위 헤더 경로 (breadcrumb)
    """
    header_marks: List[HeaderMark] = []
    stack: List[Optional[str]] = [None] * 6  # levels 1-6

    for m in HEADER_RE.finditer(text):
        level = len(m.group(1))
        title = m.group(2).strip()

        # 현재 레벨의 제목 업데이트
        stack[level - 1] = title
        # 하위 레벨 초기화
        for i in range(level, 6):
            stack[i] = None

        # 경로 생성 (None 제외)
        path = [x for x in stack if x is not None]

        header_marks.append(
            HeaderMark(
                position=m.start(),
                end_position=m.end(),
                level=level,
                title=title,
                path=path,
            )
        )

    return header_marks


# ============================================================================
# Semantic Chunking
# ============================================================================


def _split_by_paragraphs(text: str, max_size: int) -> List[str]:
    """긴 텍스트를 문단(\n\n) 단위로 분할"""
    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para)

        if current_size + para_size + 2 > max_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_size = 0

        current_chunk.append(para)
        current_size += para_size + 2  # +2 for \n\n

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def semantic_chunk(
    text: str,
    source: str,
    extra_metadata: Optional[dict] = None,  # 폴더 경로 등 추가 메타데이터
    min_size: int = MIN_CHUNK_SIZE,
    max_size: int = MAX_CHUNK_SIZE,
    chunk_level: int = 2,  # 기본 청킹 레벨 (##)
) -> List[Chunk]:
    """
    마크다운을 헤더 기반으로 Semantic Chunking.

    Args:
        text: 마크다운 텍스트
        source: 원본 파일명
        extra_metadata: 추가 메타데이터 (예: folder_path, full_path)
        min_size: 최소 청크 크기 (이보다 짧으면 병합)
        max_size: 최대 청크 크기 (이보다 길면 분할)
        chunk_level: 청킹 기준 헤더 레벨 (기본: 2 = ##)

    Returns:
        Chunk 객체 리스트
    """
    # 1. YAML frontmatter 추출
    frontmatter, body = extract_frontmatter(text)

    # 2. 코드 블록 보호
    protected_body, code_placeholders = protect_code_blocks(body)

    # 3. 헤더 추출
    header_marks = extract_header_marks(protected_body)

    if not header_marks:
        # 헤더가 없으면 전체를 하나의 청크로
        restored_body = restore_code_blocks(body, code_placeholders)
        base_metadata = {
            "source": source,
            "header_path": "",
            "headers": [],
            "frontmatter": frontmatter.__dict__ if frontmatter else None,
        }
        if extra_metadata:
            base_metadata.update(extra_metadata)
        return [Chunk(text=restored_body.strip(), metadata=base_metadata)]

    # 4. 섹션별로 텍스트 분할
    chunks: List[Chunk] = []
    pending_chunk: Optional[Tuple[str, dict]] = None  # (text, metadata)

    for i, header in enumerate(header_marks):
        # 섹션 끝 위치 결정
        if i + 1 < len(header_marks):
            end_pos = header_marks[i + 1].position
        else:
            end_pos = len(protected_body)

        section_text = protected_body[header.position : end_pos].strip()

        # 코드 블록 복원
        section_text = restore_code_blocks(section_text, code_placeholders)

        # 빈 섹션 건너뛰기
        if not section_text or section_text == header.title:
            continue

        # 메타데이터 생성
        metadata = {
            "source": source,
            "header_path": " > ".join(
                f"{'#' * (j + 1)} {h}" for j, h in enumerate(header.path)
            ),
            "headers": [header.title],
            "level": header.level,
        }

        # 추가 메타데이터 병합 (folder_path, full_path 등)
        if extra_metadata:
            metadata.update(extra_metadata)

        if frontmatter:
            metadata["frontmatter"] = {
                "tags": frontmatter.tags,
                "create_date": frontmatter.create_date,
            }

        # 청크 레벨보다 상위거나 같은 헤더에서 청킹
        if header.level <= chunk_level:
            # 이전 pending 청크가 있으면 먼저 처리
            if pending_chunk:
                ptext, pmeta = pending_chunk
                if len(ptext) > max_size:
                    # 너무 길면 분할
                    for sub in _split_by_paragraphs(ptext, max_size):
                        chunks.append(Chunk(text=sub, metadata=pmeta))
                else:
                    chunks.append(Chunk(text=ptext, metadata=pmeta))
                pending_chunk = None

            # 새 청크 시작
            pending_chunk = (section_text, metadata)
        else:
            # 하위 레벨 헤더 = 현재 pending에 병합
            if pending_chunk:
                ptext, pmeta = pending_chunk
                ptext += "\n\n" + section_text
                pmeta["headers"].append(header.title)
                pending_chunk = (ptext, pmeta)
            else:
                pending_chunk = (section_text, metadata)

    # 마지막 pending 처리
    if pending_chunk:
        ptext, pmeta = pending_chunk
        if len(ptext) < min_size:
            # 너무 짧으면 이전 청크와 병합 시도
            if chunks:
                last_chunk = chunks[-1]
                merged_text = last_chunk.text + "\n\n" + ptext
                if len(merged_text) <= max_size:
                    last_chunk.text = merged_text
                    last_chunk.metadata["headers"].extend(pmeta["headers"])
                else:
                    chunks.append(Chunk(text=ptext, metadata=pmeta))
            else:
                chunks.append(Chunk(text=ptext, metadata=pmeta))
        elif len(ptext) > max_size:
            for sub in _split_by_paragraphs(ptext, max_size):
                chunks.append(Chunk(text=sub, metadata=pmeta.copy()))
        else:
            chunks.append(Chunk(text=ptext, metadata=pmeta))

    return chunks


# ============================================================================
# File Processing
# ============================================================================


def process_markdown_file(filepath: str | Path) -> List[Chunk]:
    """
    마크다운 파일을 읽어서 청크 리스트 반환.

    Args:
        filepath: 마크다운 파일 경로

    Returns:
        Chunk 객체 리스트
    """
    path = Path(filepath)
    text = path.read_text(encoding="utf-8")
    return semantic_chunk(text, source=path.name)


def process_markdown_files(filepaths: List[str | Path]) -> List[Chunk]:
    """
    여러 마크다운 파일을 처리하여 청크 리스트 반환.

    Args:
        filepaths: 마크다운 파일 경로 리스트

    Returns:
        모든 파일의 Chunk 객체 리스트 (합쳐진)
    """
    all_chunks: List[Chunk] = []
    for filepath in filepaths:
        all_chunks.extend(process_markdown_file(filepath))
    return all_chunks
