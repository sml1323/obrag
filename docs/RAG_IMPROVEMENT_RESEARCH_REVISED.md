# Obsidian RAG 시스템 개선 연구 보고서

> 작성일: 2026-02-05
> 참조 리포지토리: ApeRAG, agentic-rag-for-dummies, Kotaemon

---

## 목차

1. [현재 시스템 분석](#1-현재-시스템-분석)
2. [한영 혼용 임베딩 문제 해결](#2-한영-혼용-임베딩-문제-해결)
3. [GraphRAG 및 지식 그래프](#3-graphrag-및-지식-그래프)
4. [Agentic RAG 패턴](#4-agentic-rag-패턴)
5. [Advanced RAG 기법](#5-advanced-rag-기법)
6. [구현 우선순위 및 로드맵](#6-구현-우선순위-및-로드맵)

---

## 1. 현재 시스템 분석

### 1.1 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                     Current Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Markdown Files                                               │
│       │                                                       │
│       ▼                                                       │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │FolderScanner│───▶│MarkdownPrep  │───▶│ semantic_chunk │  │
│  └─────────────┘    └──────────────┘    └────────────────┘  │
│                                                │              │
│                                                ▼              │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │ChromaStore  │◀───│EmbeddingStrat│◀───│   Chunks       │  │
│  │(Vector DB)  │    │(OpenAI/BGE)  │    └────────────────┘  │
│  └─────────────┘    └──────────────┘                         │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │  Retriever  │───▶│PromptBuilder │───▶│   LLMStrategy  │  │
│  └─────────────┘    └──────────────┘    └────────────────┘  │
│                                                │              │
│                                                ▼              │
│                                          RAGResponse          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 현재 구성요소

| 구성요소 | 현재 구현 | 파일 |
|---------|----------|------|
| **임베딩** | OpenAIEmbedder (default), SentenceTransformerEmbedder (BGE-m3) | `core/embedding/` |
| **벡터 DB** | ChromaDB (PersistentClient) | `db/chroma_store.py` |
| **청킹** | Header-based semantic chunking (min:200, max:1500) | `core/preprocessing/` |
| **검색** | Dense vector search (L2 distance) | `core/rag/retriever.py` |
| **LLM** | OpenAI, Gemini, Ollama | `core/llm/` |

### 1.3 현재 시스템의 한계

| 한계점 | 설명 | 영향도 |
|--------|------|--------|
| **단일 언어 임베딩** | 한글/영어 혼용 시 cross-lingual 검색 성능 저하 | 🔴 High |
| **Linear RAG** | 단순 검색→생성 파이프라인, self-correction 없음 | 🟡 Medium |
| **No Graph** | 문서 간 관계/엔티티 연결 없음 | 🟡 Medium |
| **No Reranking** | 검색 결과 재정렬 없음 | 🟡 Medium |
| **No Hybrid Search** | Dense search만 사용, keyword search 없음 | 🟡 Medium |

---

## 2. 한영 혼용 임베딩 문제 해결

### 2.1 문제 정의

```
현재 문제:
- 한글로 작성된 노트 → 영어 쿼리로 검색 시 유사도 낮음
- 영어로 작성된 노트 → 한글 쿼리로 검색 시 유사도 낮음
- 한영 혼용 문장의 일관성 없는 임베딩
```

### 2.2 해결책: Multilingual Embedding Models

#### 권장 모델 비교

| 모델 | 차원 | 한국어 성능 | 특징 | 추천도 |
|------|------|------------|------|--------|
| **multilingual-e5-large-instruct** | 1024 | ⭐⭐⭐⭐⭐ | SOTA, instruction-tuned | 🥇 1순위 |
| **BAAI/bge-m3** | 1024 | ⭐⭐⭐⭐ | Dense+Sparse+ColBERT | 🥈 2순위 |
| **dragonkue/BGE-m3-ko** | 1024 | ⭐⭐⭐⭐⭐ | 한국어 특화 fine-tuning | 🥉 3순위 |
| **Alibaba-NLP/gte-multilingual-base** | 768 | ⭐⭐⭐⭐ | 8192 토큰 컨텍스트 | 대안 |

#### 구현 예시: Multilingual E5

```python
# src/core/embedding/multilingual_embedder.py

from sentence_transformers import SentenceTransformer
from typing import List
from .strategy import EmbeddingStrategy, Vector


class MultilingualE5Embedder(EmbeddingStrategy):
    """
    Microsoft Multilingual E5 임베더.
    한국어-영어 cross-lingual retrieval에 최적화.
    """
    
    MODEL_NAME = "intfloat/multilingual-e5-large-instruct"
    
    def __init__(self, model_name: str = MODEL_NAME):
        self._model_name = model_name
        self._model = None
        self._dimension = 1024
    
    def _load_model(self):
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
    
    def embed(self, texts: List[str], is_query: bool = False) -> List[Vector]:
        """
        텍스트 임베딩 생성.
        
        Args:
            texts: 임베딩할 텍스트 리스트
            is_query: True면 쿼리용 prefix 추가
        """
        self._load_model()
        
        # E5 모델은 prefix가 중요함
        if is_query:
            texts = [f"query: {t}" for t in texts]
        else:
            texts = [f"passage: {t}" for t in texts]
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> Vector:
        """쿼리 전용 임베딩 (prefix 자동 추가)"""
        return self.embed([query], is_query=True)[0]
    
    def embed_documents(self, documents: List[str]) -> List[Vector]:
        """문서 전용 임베딩 (passage prefix 추가)"""
        return self.embed(documents, is_query=False)
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return self._model_name
```

### 2.3 Hybrid Approach: Query Translation

```python
# src/core/rag/multilingual_retriever.py

from typing import List, Optional
import asyncio


class MultilingualRetriever:
    """
    다국어 검색을 위한 하이브리드 접근.
    1. Multilingual embedding으로 직접 검색
    2. Query translation으로 추가 검색 (optional)
    """
    
    def __init__(
        self,
        store: ChromaStore,
        translator: Optional["QueryTranslator"] = None,
        enable_translation: bool = False
    ):
        self._store = store
        self._translator = translator
        self._enable_translation = enable_translation
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        languages: List[str] = ["ko", "en"]
    ) -> RetrievalResult:
        """
        다국어 하이브리드 검색.
        """
        all_results = []
        
        # 1. 원본 쿼리로 검색
        primary_results = self._store.query(query, n_results=top_k)
        all_results.extend(primary_results)
        
        # 2. 번역된 쿼리로 추가 검색 (optional)
        if self._enable_translation and self._translator:
            for lang in languages:
                translated = self._translator.translate(query, target_lang=lang)
                if translated != query:
                    secondary_results = self._store.query(translated, n_results=top_k // 2)
                    all_results.extend(secondary_results)
        
        # 3. 중복 제거 및 점수 기반 정렬
        deduplicated = self._deduplicate_by_id(all_results)
        sorted_results = sorted(deduplicated, key=lambda x: x["distance"])
        
        return self._format_results(query, sorted_results[:top_k])
```

### 2.4 ChromaStore 수정 제안

```python
# 기존 ChromaStore에 query/document prefix 지원 추가

class ChromaStore:
    def __init__(
        self,
        persist_path: str = "./chroma_db",
        collection_name: str = "obsidian_notes",
        embedder: Optional[EmbeddingStrategy] = None,
        use_instruction_prefix: bool = True  # 새 파라미터
    ):
        self._use_instruction_prefix = use_instruction_prefix
        # ... 기존 코드
    
    def query(self, query_text: str, n_results: int = 5, **kwargs):
        """쿼리 시 instruction prefix 자동 적용"""
        if self._use_instruction_prefix and hasattr(self._embedder, 'embed_query'):
            # Multilingual E5 등 instruction 모델용
            query_embedding = self._embedder.embed_query(query_text)
            return self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                **kwargs
            )
        else:
            # 기존 방식
            return self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                **kwargs
            )
```

---

## 3. GraphRAG 및 지식 그래프

### 3.0 용어 정리: Obsidian 그래프 뷰 vs GraphRAG/그래프 임베딩

- **Obsidian 그래프 뷰(로컬 그래프/태그 그래프)**: 노트/링크/태그 관계를 **시각화(UI)** 해서 사람이 탐색하기 쉽게 보여주는 기능.
- **지식 그래프(Knowledge Graph)**: 노트/섹션/태그/엔티티를 **노드**, 그 관계를 **엣지**로 저장한 데이터 구조(검색·추론에 사용).
- **그래프 임베딩(Graph Embedding)**: 그래프의 노드/엣지를 모델이 다루기 쉬운 **벡터(숫자 배열)** 로 변환해, 유사도 검색·추천·커뮤니티 탐지·재랭킹 등에 활용하는 기법.
- **GraphRAG**: (1) 문서에서 엔티티/관계를 추출해 지식 그래프를 만들고, (2) 벡터 검색 + 그래프 탐색을 결합해 컨텍스트를 강화하는 RAG 패턴.

> ✅ **중요:** GraphRAG/그래프 임베딩은 “그래프를 그려주는 기능”이 아니라, **그래프(구조 데이터)를 검색/추론 성능 향상에 쓰는 방법**입니다.  
> ✅ **위키링크를 많이 안 써도 가능:** 태그(`#tag`), 헤더(`#`, `##`), 파일 경로/폴더, LLM 기반 엔티티 추출로도 그래프를 만들 수 있습니다.

### 3.1 GraphRAG 개요

```
┌─────────────────────────────────────────────────────────────┐
│                      GraphRAG Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Documents ──▶ Entity Extraction ──▶ Knowledge Graph         │
│                      │                      │                 │
│                      ▼                      ▼                 │
│              Relationship Extraction   Community Detection    │
│                      │                      │                 │
│                      └──────────┬───────────┘                 │
│                                 ▼                             │
│                    ┌─────────────────────┐                    │
│                    │   Hybrid Search     │                    │
│                    │  Vector + Graph     │                    │
│                    └─────────────────────┘                    │
│                                 │                             │
│                                 ▼                             │
│                          Enhanced Context                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Obsidian 특화 Entity Extraction

Obsidian의 구조를 활용한 엔티티 추출:

```python
# src/core/graph/obsidian_entity_extractor.py

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Entity:
    name: str
    type: str  # concept, person, tool, etc.
    description: str
    source_file: str


@dataclass
class Relationship:
    source: str
    target: str
    type: str  # links_to, mentions, related_to
    weight: float


class ObsidianEntityExtractor:
    """
    Obsidian 마크다운에서 엔티티와 관계 추출.
    Obsidian 특유의 문법 활용.
    """
    
    # Obsidian 문법 패턴
    WIKILINK_PATTERN = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    TAG_PATTERN = r'#([a-zA-Z가-힣][a-zA-Z0-9가-힣_/-]*)'
    HEADER_PATTERN = r'^(#{1,6})\s+(.+)$'
    
    def extract_from_markdown(
        self,
        content: str,
        source_file: str
    ) -> Tuple[List[Entity], List[Relationship]]:
        """마크다운에서 엔티티와 관계 추출"""
        entities = []
        relationships = []
        
        # 1. Wikilinks → Entity + Relationship
        wikilinks = re.findall(self.WIKILINK_PATTERN, content)
        for link in wikilinks:
            entities.append(Entity(
                name=link,
                type="linked_note",
                description=f"Linked from {source_file}",
                source_file=source_file
            ))
            relationships.append(Relationship(
                source=source_file,
                target=link,
                type="links_to",
                weight=1.0
            ))
        
        # 2. Tags → Entity (category)
        tags = re.findall(self.TAG_PATTERN, content)
        for tag in tags:
            tag_name = f"#{tag}"
            entities.append(Entity(
                name=tag_name,
                type="tag",
                description=f"Tag used in {source_file}",
                source_file=source_file
            ))
            # 위키링크가 없어도 그래프를 만들 수 있도록 관계를 추가
            relationships.append(Relationship(
                source=source_file,
                target=tag_name,
                type="tagged_with",
                weight=0.6
            ))

        # 3. Headers → Entity (concept)
        for match in re.finditer(self.HEADER_PATTERN, content, re.MULTILINE):
            level, header_text = match.groups()
            concept = header_text.strip()
            entities.append(Entity(
                name=concept,
                type="concept",
                description=f"Section header in {source_file}",
                source_file=source_file
            ))
            relationships.append(Relationship(
                source=source_file,
                target=concept,
                type="has_section",
                weight=0.4
            ))

        return entities, relationships
    
    def extract_with_llm(
        self,
        content: str,
        source_file: str,
        llm: "LLMStrategy"
    ) -> Tuple[List[Entity], List[Relationship]]:
        """LLM을 활용한 심층 엔티티 추출"""
        prompt = f"""
        다음 마크다운 문서에서 주요 엔티티와 관계를 추출하세요.
        
        문서:
        {content[:2000]}
        
        응답 형식 (JSON):
        {{
            "entities": [
                {{"name": "...", "type": "person|concept|tool|organization", "description": "..."}}
            ],
            "relationships": [
                {{"source": "...", "target": "...", "type": "...", "description": "..."}}
            ]
        }}
        """
        # LLM 호출 및 파싱
        # ...
```

### 3.3 Graph Storage: Neo4j vs NetworkX

| 용도 | 권장 | 이유 |
|------|------|------|
| 개발/프로토타이핑 | NetworkX | 설치 간단, 메모리 기반 |
| 프로덕션 (<10K 노드) | SQLite + JSON | 간단, 별도 서버 불필요 |
| 프로덕션 (>10K 노드) | Neo4j | 쿼리 최적화, 확장성 |

#### 간단한 Graph Store (SQLite 기반)

```python
# src/db/graph_store.py

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any


class SimpleGraphStore:
    """
    SQLite 기반 간단한 그래프 저장소.
    소규모 Obsidian vault에 적합.
    """
    
    def __init__(self, db_path: str = "./graph.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT,
                    description TEXT,
                    properties TEXT,  -- JSON
                    embedding BLOB    -- Optional: entity embedding
                );
                
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT,
                    weight REAL DEFAULT 1.0,
                    properties TEXT,  -- JSON
                    FOREIGN KEY (source_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id);
                CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id);
                CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type);
            """)
    
    def add_entity(self, entity: Dict[str, Any]) -> str:
        """엔티티 추가/업데이트"""
        entity_id = entity.get("id") or self._generate_id(entity["name"])
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO entities (id, name, type, description, properties)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entity_id,
                entity["name"],
                entity.get("type"),
                entity.get("description"),
                json.dumps(entity.get("properties", {}))
            ))
        return entity_id
    
    def add_relationship(self, rel: Dict[str, Any]) -> str:
        """관계 추가"""
        rel_id = f"{rel['source']}--{rel['type']}--{rel['target']}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO relationships 
                (id, source_id, target_id, type, weight, properties)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rel_id,
                rel["source"],
                rel["target"],
                rel.get("type", "related_to"),
                rel.get("weight", 1.0),
                json.dumps(rel.get("properties", {}))
            ))
        return rel_id
    
    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[Dict]:
        """엔티티의 이웃 노드 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT e.*, r.type as rel_type, r.weight
                FROM entities e
                JOIN relationships r ON (r.target_id = e.id OR r.source_id = e.id)
                WHERE r.source_id = ? OR r.target_id = ?
            """, (entity_id, entity_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_entity_by_name(self, name: str) -> Dict | None:
        """이름으로 엔티티 검색"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM entities WHERE name = ?", (name,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
```

### 3.4 Graph Visualization (Frontend)

```typescript
// front/components/knowledge-graph.tsx

"use client";

import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

interface GraphNode {
  id: string;
  label: string;
  type: string;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

interface KnowledgeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
}

export function KnowledgeGraph({ nodes, edges, onNodeClick }: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements = [
      // Nodes
      ...nodes.map((node) => ({
        data: { id: node.id, label: node.label, type: node.type },
      })),
      // Edges
      ...edges.map((edge) => ({
        data: {
          id: `${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          label: edge.label,
        },
      })),
    ];

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#6366f1",
            label: "data(label)",
            color: "#fff",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "12px",
          },
        },
        {
          selector: "node[type='tag']",
          style: { "background-color": "#22c55e" },
        },
        {
          selector: "node[type='concept']",
          style: { "background-color": "#f59e0b" },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
          },
        },
      ],
      layout: { name: "cose", animate: true },
    });

    if (onNodeClick) {
      cyRef.current.on("tap", "node", (evt) => {
        onNodeClick(evt.target.id());
      });
    }

    return () => {
      cyRef.current?.destroy();
    };
  }, [nodes, edges, onNodeClick]);

  return (
    <div
      ref={containerRef}
      className="w-full h-[500px] border rounded-lg bg-slate-50"
    />
  );
}
```

### 3.5 Hybrid Search: Vector + Graph

```python
# src/core/rag/hybrid_graph_retriever.py

from typing import List, Set
from dataclasses import dataclass


@dataclass
class HybridResult:
    chunk_id: str
    text: str
    score: float
    graph_context: List[str]  # 연결된 엔티티들


class HybridGraphRetriever:
    """
    Vector Search + Graph Traversal 하이브리드 검색.
    """
    
    def __init__(
        self,
        vector_store: "ChromaStore",
        graph_store: "SimpleGraphStore",
        graph_weight: float = 0.3
    ):
        self._vector_store = vector_store
        self._graph_store = graph_store
        self._graph_weight = graph_weight
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        graph_depth: int = 1
    ) -> List[HybridResult]:
        """
        1. Vector search로 초기 결과 획득
        2. 결과에서 엔티티 추출
        3. Graph traversal로 관련 엔티티 확장
        4. 확장된 컨텍스트 포함하여 반환
        """
        # 1. Vector search
        vector_results = self._vector_store.query(query, n_results=top_k * 2)
        
        # 2. 결과에서 엔티티 추출
        entities: Set[str] = set()
        for result in vector_results:
            source = result["metadata"].get("source", "")
            if source:
                entities.add(source.replace(".md", ""))
        
        # 3. Graph traversal
        expanded_entities = set()
        for entity_name in entities:
            entity = self._graph_store.get_entity_by_name(entity_name)
            if entity:
                neighbors = self._graph_store.get_neighbors(
                    entity["id"], depth=graph_depth
                )
                for neighbor in neighbors:
                    expanded_entities.add(neighbor["name"])
        
        # 4. 결과 구성
        results = []
        for result in vector_results[:top_k]:
            graph_context = list(expanded_entities)[:5]  # 상위 5개
            results.append(HybridResult(
                chunk_id=result["id"],
                text=result["text"],
                score=1 / (1 + result["distance"]),
                graph_context=graph_context
            ))
        
        return results
```

---

## 4. Agentic RAG 패턴

### 4.1 Simple RAG vs Agentic RAG

```
Simple RAG (현재):
Query → Vector Search → Context → LLM → Response

Agentic RAG:
Query → Conversation Analysis → Query Clarification → 
     → Parallel Retrieval → Self-Correction → Response Synthesis
```

### 4.2 핵심 Agentic 패턴

#### 패턴 1: Query Rewriting

```python
# src/core/rag/agentic/query_rewriter.py

from typing import List, Tuple


class QueryRewriter:
    """
    대화 컨텍스트를 고려한 쿼리 재작성.
    - 모호한 참조 해결 (예: "그것" → "API 인증 방법")
    - 복잡한 질문 분할
    """
    
    REWRITE_PROMPT = """
    당신은 쿼리 분석 전문가입니다.
    
    대화 이력:
    {history}
    
    현재 질문:
    {query}
    
    규칙:
    1. 질문이 모호하면 대화 이력을 참조해 명확하게 재작성
    2. 복잡한 질문은 최대 3개의 하위 질문으로 분할
    3. 분할 불필요시 원본 질문 그대로 반환
    
    응답 형식 (JSON):
    {{
        "is_clear": true/false,
        "rewritten_queries": ["질문1", "질문2", ...],
        "clarification_needed": "명확화 필요시 요청할 내용 (없으면 null)"
    }}
    """
    
    def __init__(self, llm: "LLMStrategy"):
        self._llm = llm
    
    def rewrite(
        self,
        query: str,
        history: List["Message"] = None
    ) -> Tuple[bool, List[str], str | None]:
        """
        쿼리 재작성.
        
        Returns:
            (is_clear, rewritten_queries, clarification_request)
        """
        history_text = self._format_history(history or [])
        prompt = self.REWRITE_PROMPT.format(
            history=history_text,
            query=query
        )
        
        response = self._llm.generate([
            {"role": "user", "content": prompt}
        ])
        
        result = self._parse_response(response.content)
        return (
            result.get("is_clear", True),
            result.get("rewritten_queries", [query]),
            result.get("clarification_needed")
        )
```

#### 패턴 2: Self-Correction (Retry Logic)

```python
# src/core/rag/agentic/self_correcting_chain.py

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CorrectionResult:
    answer: str
    attempts: int
    final_query: str
    retrieval_quality: float


class SelfCorrectingRAGChain:
    """
    검색 결과가 불충분할 때 자동으로 재시도하는 RAG 체인.
    """
    
    QUALITY_THRESHOLD = 0.6
    MAX_RETRIES = 2
    
    def __init__(
        self,
        retriever: "Retriever",
        llm: "LLMStrategy",
        query_rewriter: "QueryRewriter"
    ):
        self._retriever = retriever
        self._llm = llm
        self._query_rewriter = query_rewriter
    
    def query(self, question: str, **kwargs) -> CorrectionResult:
        """
        Self-correcting RAG 쿼리.
        
        1. 초기 검색 수행
        2. 결과 품질 평가
        3. 품질 낮으면 쿼리 재작성 후 재시도
        """
        current_query = question
        attempts = 0
        
        while attempts <= self.MAX_RETRIES:
            attempts += 1
            
            # 검색 수행
            result = self._retriever.retrieve(current_query, top_k=5)
            
            # 품질 평가
            quality = self._evaluate_quality(result, current_query)
            
            if quality >= self.QUALITY_THRESHOLD:
                # 충분한 품질 → 응답 생성
                answer = self._generate_answer(current_query, result)
                return CorrectionResult(
                    answer=answer,
                    attempts=attempts,
                    final_query=current_query,
                    retrieval_quality=quality
                )
            
            if attempts <= self.MAX_RETRIES:
                # 쿼리 재작성
                current_query = self._broaden_query(current_query)
        
        # 최대 재시도 후에도 실패 → 최선의 결과로 응답
        answer = self._generate_answer(current_query, result)
        return CorrectionResult(
            answer=answer,
            attempts=attempts,
            final_query=current_query,
            retrieval_quality=quality
        )
    
    def _evaluate_quality(
        self,
        result: "RetrievalResult",
        query: str
    ) -> float:
        """검색 결과 품질 평가 (0~1)"""
        if not result.chunks:
            return 0.0
        
        # 상위 결과의 평균 score
        top_scores = [c.score for c in result.chunks[:3]]
        avg_score = sum(top_scores) / len(top_scores)
        
        return avg_score
    
    def _broaden_query(self, query: str) -> str:
        """쿼리를 더 넓은 범위로 재작성"""
        prompt = f"""
        다음 검색 쿼리가 결과를 찾지 못했습니다.
        더 넓은 범위로 재작성해주세요.
        
        원본 쿼리: {query}
        
        재작성된 쿼리:
        """
        response = self._llm.generate([{"role": "user", "content": prompt}])
        return response.content.strip()
```

#### 패턴 3: Parallel Query Processing

```python
# src/core/rag/agentic/parallel_retriever.py

import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor


class ParallelQueryProcessor:
    """
    복잡한 질문을 분할하여 병렬 처리.
    """
    
    def __init__(
        self,
        retriever: "Retriever",
        max_workers: int = 3
    ):
        self._retriever = retriever
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_queries(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> List["RetrievalResult"]:
        """여러 쿼리 병렬 처리"""
        futures = [
            self._executor.submit(self._retriever.retrieve, q, top_k)
            for q in queries
        ]
        return [f.result() for f in futures]
    
    async def process_queries_async(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> List["RetrievalResult"]:
        """Async 버전"""
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self._executor,
                self._retriever.retrieve,
                q,
                top_k
            )
            for q in queries
        ]
        return await asyncio.gather(*tasks)
    
    def aggregate_results(
        self,
        results: List["RetrievalResult"],
        top_k: int = 5
    ) -> "RetrievalResult":
        """여러 결과를 하나로 병합"""
        all_chunks = []
        seen_ids = set()
        
        for result in results:
            for chunk in result.chunks:
                if chunk.id not in seen_ids:
                    all_chunks.append(chunk)
                    seen_ids.add(chunk.id)
        
        # Score로 정렬
        all_chunks.sort(key=lambda c: c.score, reverse=True)
        
        return RetrievalResult(
            query="[merged]",
            chunks=all_chunks[:top_k],
            total_count=len(all_chunks)
        )
```

### 4.3 Hierarchical Indexing (Parent-Child Chunks)

```python
# src/core/preprocessing/hierarchical_chunker.py

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HierarchicalChunk:
    id: str
    text: str
    metadata: dict
    parent_id: Optional[str] = None
    children_ids: List[str] = None


class HierarchicalChunker:
    """
    Parent-Child 청크 계층 구조.
    - Parent: 큰 섹션 (헤더 기반)
    - Child: 작은 청크 (검색용, 500자)
    
    검색 시: Child로 정밀 검색 → Parent로 컨텍스트 확장
    """
    
    def __init__(
        self,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 500,
        child_overlap: int = 50
    ):
        self.parent_size = parent_chunk_size
        self.child_size = child_chunk_size
        self.child_overlap = child_overlap
    
    def chunk(
        self,
        text: str,
        source: str
    ) -> tuple[List[HierarchicalChunk], List[HierarchicalChunk]]:
        """
        Returns:
            (parent_chunks, child_chunks)
        """
        parents = []
        children = []
        
        # 1. Parent 청크 생성 (헤더 기반)
        parent_chunks = self._create_parent_chunks(text, source)
        parents.extend(parent_chunks)
        
        # 2. 각 Parent에서 Child 청크 생성
        for parent in parent_chunks:
            child_chunks = self._split_to_children(parent)
            children.extend(child_chunks)
        
        return parents, children
    
    def _create_parent_chunks(
        self,
        text: str,
        source: str
    ) -> List[HierarchicalChunk]:
        """헤더 기반 Parent 청크 생성"""
        # 기존 semantic_chunk 로직 활용
        from core.preprocessing import semantic_chunk
        chunks = semantic_chunk(
            text=text,
            source=source,
            min_size=500,
            max_size=self.parent_size
        )
        return [
            HierarchicalChunk(
                id=f"{source}::parent_{i}",
                text=c.text,
                metadata=c.metadata,
                children_ids=[]
            )
            for i, c in enumerate(chunks)
        ]
    
    def _split_to_children(
        self,
        parent: HierarchicalChunk
    ) -> List[HierarchicalChunk]:
        """Parent를 작은 Child 청크로 분할"""
        text = parent.text
        children = []
        
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.child_size, len(text))
            child_text = text[start:end]
            
            child = HierarchicalChunk(
                id=f"{parent.id}::child_{idx}",
                text=child_text,
                metadata={**parent.metadata, "parent_id": parent.id},
                parent_id=parent.id
            )
            children.append(child)
            parent.children_ids.append(child.id)
            
            start = end - self.child_overlap
            idx += 1
        
        return children
```

---

## 5. Advanced RAG 기법

### 5.1 Hybrid Search (Dense + Sparse)

```python
# src/core/rag/hybrid_search.py

from rank_bm25 import BM25Okapi
import numpy as np
from typing import List


class HybridSearcher:
    """
    Dense (Vector) + Sparse (BM25) 하이브리드 검색.
    """
    
    def __init__(
        self,
        vector_store: "ChromaStore",
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3
    ):
        self._vector_store = vector_store
        self._dense_weight = dense_weight
        self._sparse_weight = sparse_weight
        self._bm25 = None
        self._documents = []
    
    def index_documents(self, documents: List[str], ids: List[str]):
        """BM25 인덱스 구축"""
        self._documents = documents
        self._doc_ids = ids
        tokenized = [doc.lower().split() for doc in documents]
        self._bm25 = BM25Okapi(tokenized)
    
    def search(self, query: str, top_k: int = 10) -> List[dict]:
        """하이브리드 검색"""
        # 1. Dense search
        dense_results = self._vector_store.query(query, n_results=top_k * 2)
        dense_scores = {
            r["id"]: 1 / (1 + r["distance"])
            for r in dense_results
        }
        
        # 2. Sparse search (BM25)
        tokenized_query = query.lower().split()
        bm25_scores = self._bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        sparse_scores = {
            self._doc_ids[i]: score / max_bm25
            for i, score in enumerate(bm25_scores)
        }
        
        # 3. Combine scores
        all_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
        combined = []
        
        for doc_id in all_ids:
            d_score = dense_scores.get(doc_id, 0)
            s_score = sparse_scores.get(doc_id, 0)
            final_score = (
                self._dense_weight * d_score +
                self._sparse_weight * s_score
            )
            combined.append({
                "id": doc_id,
                "score": final_score,
                "dense_score": d_score,
                "sparse_score": s_score
            })
        
        # Sort by combined score
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]
```

### 5.2 Reranking with Cross-Encoder

```python
# src/core/rag/reranker.py

from sentence_transformers import CrossEncoder
from typing import List


class Reranker:
    """
    Cross-Encoder 기반 재순위화.
    초기 검색 결과를 더 정밀하게 정렬.
    """
    
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self._model_name = model_name
        self._model = None
    
    def _load_model(self):
        if self._model is None:
            self._model = CrossEncoder(self._model_name)
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[tuple[str, float]]:
        """
        문서 재순위화.
        
        Returns:
            [(document, score), ...] 정렬된 리스트
        """
        self._load_model()
        
        # Query-Document 쌍 생성
        pairs = [(query, doc) for doc in documents]
        
        # Cross-Encoder 점수 계산
        scores = self._model.predict(pairs)
        
        # 정렬
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        return doc_scores[:top_k]


class RerankedRetriever:
    """Reranking을 적용한 Retriever 래퍼"""
    
    def __init__(
        self,
        base_retriever: "Retriever",
        reranker: "Reranker",
        initial_k: int = 20
    ):
        self._base = base_retriever
        self._reranker = reranker
        self._initial_k = initial_k
    
    def retrieve(self, query: str, top_k: int = 5) -> "RetrievalResult":
        # 1. 초기 검색 (더 많이)
        initial_result = self._base.retrieve(query, top_k=self._initial_k)
        
        # 2. Rerank
        documents = [c.text for c in initial_result.chunks]
        reranked = self._reranker.rerank(query, documents, top_k=top_k)
        
        # 3. 결과 재구성
        reranked_chunks = []
        for doc_text, score in reranked:
            for chunk in initial_result.chunks:
                if chunk.text == doc_text:
                    chunk.score = score  # Update score
                    reranked_chunks.append(chunk)
                    break
        
        return RetrievalResult(
            query=query,
            chunks=reranked_chunks,
            total_count=len(reranked_chunks)
        )
```

### 5.3 Query Expansion

```python
# src/core/rag/query_expansion.py

from typing import List


class QueryExpander:
    """
    쿼리 확장으로 검색 recall 향상.
    - 동의어 추가
    - 관련 용어 생성
    """
    
    EXPANSION_PROMPT = """
    다음 검색 쿼리에 대해 관련 검색어를 생성하세요.
    동의어, 관련 개념, 다른 표현을 포함해주세요.
    
    원본 쿼리: {query}
    
    확장 검색어 (쉼표로 구분, 최대 5개):
    """
    
    def __init__(self, llm: "LLMStrategy"):
        self._llm = llm
    
    def expand(self, query: str, max_terms: int = 5) -> List[str]:
        """쿼리를 확장하여 관련 검색어 생성"""
        prompt = self.EXPANSION_PROMPT.format(query=query)
        response = self._llm.generate([{"role": "user", "content": prompt}])
        
        # 파싱
        terms = [t.strip() for t in response.content.split(",")]
        return [query] + terms[:max_terms]
    
    def expand_for_multilingual(
        self,
        query: str,
        languages: List[str] = ["ko", "en"]
    ) -> List[str]:
        """다국어 확장"""
        expanded = [query]
        
        for lang in languages:
            if lang == "ko":
                # 한글 동의어/관련어 추가
                korean_terms = self._get_korean_synonyms(query)
                expanded.extend(korean_terms)
            elif lang == "en":
                # 영어 동의어/관련어 추가
                english_terms = self._get_english_synonyms(query)
                expanded.extend(english_terms)
        
        return list(set(expanded))  # 중복 제거
```

---

## 6. 구현 우선순위 및 로드맵

### 6.1 우선순위 매트릭스

| 기능 | 영향도 | 복잡도 | 우선순위 | 예상 기간 |
|------|--------|--------|----------|----------|
| **Multilingual Embedding (E5)** | 🔴 High | 🟢 Low | 🥇 1순위 | 1-2일 |
| **Hybrid Search (Dense+Sparse)** | 🟡 Medium | 🟢 Low | 🥈 2순위 | 2-3일 |
| **Reranking** | 🟡 Medium | 🟢 Low | 🥉 3순위 | 1-2일 |
| **Query Rewriting (Agentic)** | 🟡 Medium | 🟡 Medium | 4순위 | 3-5일 |
| **Self-Correction** | 🟡 Medium | 🟡 Medium | 5순위 | 2-3일 |
| **Graph Entity Extraction** | 🟡 Medium | 🟡 Medium | 6순위 | 5-7일 |
| **Graph Visualization** | 🟢 Low | 🟡 Medium | 7순위 | 3-5일 |
| **Full GraphRAG** | 🟡 Medium | 🔴 High | 8순위 | 2-3주 |

### 6.2 Phase별 로드맵

#### Phase 1: Core Improvements (1-2주)

```
Week 1:
├── Day 1-2: Multilingual E5 Embedder 구현
├── Day 3-4: Hybrid Search (BM25 추가)
└── Day 5: Reranker 통합

Week 2:
├── Day 1-2: Query prefix 지원 (query:/passage:)
├── Day 3-4: 테스트 및 벤치마크
└── Day 5: 문서화
```

**산출물:**
- `MultilingualE5Embedder` 클래스
- `HybridSearcher` 클래스
- `Reranker` 클래스
- 한영 교차 검색 성능 개선

#### Phase 2: Agentic Features (2-3주)

```
Week 3-4:
├── Query Rewriting 시스템
├── Self-Correction 로직
├── Parallel Query Processing
└── Hierarchical Chunking (Parent-Child)
```

**산출물:**
- `QueryRewriter` 클래스
- `SelfCorrectingRAGChain` 클래스
- `ParallelQueryProcessor` 클래스
- 복잡한 질문 처리 능력 향상

#### Phase 3: Graph Integration (3-4주)

```
Week 5-7:
├── Obsidian Entity Extractor
├── SimpleGraphStore (SQLite)
├── Hybrid Graph Retriever
├── Graph API Endpoints
└── Frontend Graph Visualization
```

**산출물:**
- Knowledge Graph 구축 파이프라인
- Graph + Vector 하이브리드 검색
- Interactive Graph UI

### 6.3 빠른 시작: 1순위 구현

즉시 적용 가능한 Multilingual Embedding 변경:

```python
# 1. requirements.txt에 추가
# sentence-transformers>=2.2.0

# 2. src/core/embedding/__init__.py 수정
from .multilingual_embedder import MultilingualE5Embedder

# 3. 사용
embedder = MultilingualE5Embedder()
store = ChromaStore(embedder=embedder)

# 한글로 작성된 노트, 영어로 검색 가능
results = store.query("How to authenticate API?")  # 한글 노트도 검색됨
```

---

## 참고 자료

### 연구 논문
- [BGE M3-Embedding](https://arxiv.org/abs/2402.03216) - Multi-Lingual, Multi-Functionality Text Embeddings
- [GraphRAG](https://arxiv.org/abs/2404.16130) - From Local to Global: A Graph RAG Approach
- [RankRAG](https://arxiv.org/abs/2407.02485) - Unifying Context Ranking with RAG

### 오픈소스 프로젝트
- [ApeRAG](https://github.com/apecloud/ApeRAG) - Production-grade RAG with Graph support
- [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies) - Agentic RAG patterns
- [Kotaemon](https://github.com/Cinnamon/kotaemon) - RAG-based QA with UI
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag) - Official GraphRAG implementation

### 모델
- [intfloat/multilingual-e5-large-instruct](https://huggingface.co/intfloat/multilingual-e5-large-instruct)
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)
- [dragonkue/BGE-m3-ko](https://huggingface.co/dragonkue/BGE-m3-ko)
