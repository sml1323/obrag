# ChromaStore

청크를 벡터화하여 ChromaDB에 저장하고 유사도 검색을 수행하는 모듈입니다.

---

## 🔄 Processing Pipeline
![chroma_store](../../docs/images/chromadb.png)

[code link](../../src/db/chroma_store.py)

---

## 📦 Classes

### \_EmbeddingFunctionAdapter

EmbeddingStrategy를 ChromaDB EmbeddingFunction 인터페이스로 변환하는 어댑터.

| Method        | Description                       |
| ------------- | --------------------------------- |
| `__call__`    | ChromaDB 문서 추가 시 임베딩 수행 |
| `embed_query` | ChromaDB 쿼리 시 임베딩 수행      |
| `name`        | 어댑터 이름 반환                  |

### ChromaStore

| Field             | Type                | Description                |
| ----------------- | ------------------- | -------------------------- |
| `persist_path`    | `Path`              | 데이터 저장 경로           |
| `collection_name` | `str`               | ChromaDB 컬렉션 이름       |
| `_embedder`       | `EmbeddingStrategy` | 임베딩 전략 (기본: OpenAI) |
| `_collection`     | `Collection`        | ChromaDB 컬렉션 객체       |

---

## 🔧 Methods

### 1️⃣ **init**()

ChromaStore 인스턴스를 생성합니다.

| Parameter         | Type                | Default            | Description            |
| ----------------- | ------------------- | ------------------ | ---------------------- |
| `persist_path`    | `str`               | `"./chroma_db"`    | 데이터 저장 경로       |
| `collection_name` | `str`               | `"obsidian_notes"` | 컬렉션 이름            |
| `embedder`        | `EmbeddingStrategy` | `None`             | 임베딩 전략 (Optional) |

<details>
<summary><b>사용 예시</b></summary>

```python
from db.chroma_store import ChromaStore
from core.embedding import FakeEmbedder

# 기본 (OpenAI 임베딩)
store = ChromaStore()

# Custom embedder
store = ChromaStore(embedder=FakeEmbedder())
```

</details>

---

### 2️⃣ add_chunks()

청크 리스트를 DB에 저장합니다. (자동 ID 생성)

<details>
<summary><b>Input/Output 예시</b></summary>

**Input:**

```python
from core.preprocessing import Chunk

chunks = [
    Chunk(text="## Architecture\nTransformer...", metadata={"source": "note.md"}),
    Chunk(text="## Training\nProcess...", metadata={"source": "note.md"}),
]

count = store.add_chunks(chunks)
```

**Output:** `int` (저장된 청크 수)

```python
2
```

</details>

---

### 3️⃣ upsert_chunks() ⭐ 증분 동기화용

청크를 upsert합니다. (있으면 업데이트, 없으면 추가)

| Parameter       | Type   | Description                          |
| --------------- | ------ | ------------------------------------ |
| `chunks`        | `List` | Chunk 객체 리스트                    |
| `relative_path` | `str`  | 루트 기준 상대 경로 (ID 생성에 사용) |

<details>
<summary><b>Input/Output 예시</b></summary>

**Input:**

```python
chunks = [Chunk(text="Updated content...", metadata={...})]

count = store.upsert_chunks(chunks, relative_path="folder/note.md")
```

**Output:** `int`

```python
1  # upsert된 청크 수
```

**생성되는 ID 형식:**

```
"folder/note.md::chunk_0"
"folder/note.md::chunk_1"
```

</details>

---

### 4️⃣ query() ⭐ 핵심 함수

텍스트 쿼리로 유사 청크를 검색합니다.

| Parameter        | Type   | Default    | Description     |
| ---------------- | ------ | ---------- | --------------- |
| `query_text`     | `str`  | _required_ | 검색 쿼리       |
| `n_results`      | `int`  | `5`        | 반환할 결과 수  |
| `where`          | `dict` | `None`     | 메타데이터 필터 |
| `where_document` | `dict` | `None`     | 문서 내용 필터  |

<details>
<summary><b>Input/Output 예시</b></summary>

**Input:**

```python
results = store.query(
    query_text="Transformer architecture",
    n_results=3,
    where={"source": "transformer.md"}
)
```

**Output:** `List[dict]`

```python
[
    {
        "id": "transformer.md_0_a1b2c3d4",
        "text": "## Architecture\nThe transformer architecture...",
        "metadata": {"source": "transformer.md", "headers": ["Architecture"]},
        "distance": 0.123
    },
    {
        "id": "transformer.md_1_e5f6g7h8",
        "text": "## Encoder\nEncoder details...",
        "metadata": {"source": "transformer.md", "headers": ["Encoder"]},
        "distance": 0.456
    }
]
```

</details>

---

### 5️⃣ get_stats()

컬렉션 통계를 반환합니다.

```python
stats = store.get_stats()
# {"name": "obsidian_notes", "count": 150, "persist_path": "/path/to/db", "embedder": "OpenAIEmbedder()"}
```

---

### 6️⃣ clear()

컬렉션 내 모든 데이터를 삭제합니다.

```python
store.clear()  # 모든 청크 삭제
```

---

### 7️⃣ delete_by_source()

특정 source 파일의 모든 청크를 삭제합니다.

```python
store.delete_by_source("old_note.md")
```

---

### 8️⃣ delete_by_relative_path()

특정 relative_path의 모든 청크를 삭제합니다. (증분 동기화용)

```python
store.delete_by_relative_path("folder/deleted_note.md")
```

---

### 9️⃣ delete_chunks_by_prefix()

특정 파일의 특정 인덱스 이상 청크를 삭제합니다.

파일 수정 후 청크 수가 줄었을 때 초과 청크 정리에 사용됩니다.

```python
# chunk_3 이상 모두 삭제 (chunk_0, chunk_1, chunk_2만 유지)
store.delete_chunks_by_prefix("folder/note.md", from_index=3)
```

---

## 🛠 Static Methods

### generate_deterministic_id()

파일 경로 + 청크 인덱스 기반 deterministic ID를 생성합니다.

```python
chunk_id = ChromaStore.generate_deterministic_id("folder/note.md", 0)
# "folder/note.md::chunk_0"
```

---

## 🚀 Quick Start

```python
from db.chroma_store import ChromaStore, create_store, store_chunks, search_chunks
from core.preprocessing import semantic_chunk

# 방법 1: 클래스 직접 사용
store = ChromaStore(persist_path="./my_db")
text = open("document.md").read()
chunks = semantic_chunk(text=text, source="document.md")
store.add_chunks(chunks)

results = store.query("검색어", n_results=5)
for r in results:
    print(f"Distance: {r['distance']:.3f}")
    print(f"Text: {r['text'][:100]}...")

# 방법 2: 편의 함수 사용
store_chunks(chunks, persist_path="./my_db")
results = search_chunks("검색어", n_results=5, persist_path="./my_db")
```

---

## 🔗 Convenience Functions

| Function        | Description                 |
| --------------- | --------------------------- |
| `create_store`  | ChromaStore 인스턴스 생성   |
| `store_chunks`  | 청크를 ChromaDB에 저장      |
| `search_chunks` | ChromaDB에서 유사 청크 검색 |

---

## 🔗 Related Modules

- **[EmbeddingStrategy](../../src/core/embedding/)** - 임베딩 전략 인터페이스
- **[MarkdownPreprocessor](./markdown_preprocessor.md)** - 청크 생성
- **[test_chroma_store.py](../../src/tasktests/phase1/test_chroma_store.py)** - 테스트 스크립트
