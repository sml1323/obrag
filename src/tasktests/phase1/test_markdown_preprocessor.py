"""
Phase 1: Markdown Preprocessor 테스트

이 테스트는 헤더 기반 Semantic Chunking이 올바르게 동작하는지 검증합니다.
테스트 대상: src/core/preprocessing/markdown_preprocessor.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from core.preprocessing import (
    Chunk,
    HeaderMark,
    YAMLFrontmatter,
    extract_frontmatter,
    extract_header_marks,
    process_markdown_file,
    protect_code_blocks,
    restore_code_blocks,
    semantic_chunk,
)


# ============================================================================
# Test: YAML Frontmatter
# ============================================================================

class TestYAMLFrontmatter:
    """YAML frontmatter 추출 테스트"""
    
    def test_extract_frontmatter_with_tags(self):
        """태그가 있는 frontmatter 추출"""
        text = """---
tags:
  - transformer
  - llm
create: 2025-11-16 12:43:42
---
# Title
Content here
"""
        frontmatter, body = extract_frontmatter(text)
        
        assert frontmatter is not None
        assert frontmatter.tags == ["transformer", "llm"]
        assert frontmatter.create_date == "2025-11-16 12:43:42"
        assert body.strip().startswith("# Title")
    
    def test_extract_frontmatter_without_frontmatter(self):
        """frontmatter가 없는 경우"""
        text = "# Title\nContent"
        frontmatter, body = extract_frontmatter(text)
        
        assert frontmatter is None
        assert body == text
    
    def test_extract_frontmatter_empty(self):
        """빈 frontmatter"""
        text = """---
---
# Title
"""
        frontmatter, body = extract_frontmatter(text)
        
        assert frontmatter is not None
        assert frontmatter.tags == []
        assert body.strip() == "# Title"


# ============================================================================
# Test: Code Block Protection
# ============================================================================

class TestCodeBlockProtection:
    """코드 블록 보호 테스트"""
    
    def test_protect_single_code_block(self):
        """단일 코드 블록 보호"""
        text = """Some text
```python
def hello():
    print("world")
```
More text"""
        
        protected, placeholders = protect_code_blocks(text)
        
        assert "__CODE_BLOCK_0__" in protected
        assert len(placeholders) == 1
        assert "def hello():" in placeholders[0][1]
    
    def test_protect_multiple_code_blocks(self):
        """여러 코드 블록 보호"""
        text = """```python
code1
```
text
```javascript
code2
```"""
        
        protected, placeholders = protect_code_blocks(text)
        
        assert len(placeholders) == 2
        assert "__CODE_BLOCK_0__" in protected
        assert "__CODE_BLOCK_1__" in protected
    
    def test_restore_code_blocks(self):
        """코드 블록 복원"""
        original = """```python
hello
```"""
        protected, placeholders = protect_code_blocks(original)
        restored = restore_code_blocks(protected, placeholders)
        
        assert restored == original
    
    def test_nested_backticks(self):
        """중첩 백틱 (````로 감싼 경우)"""
        text = """````python
```nested```
````"""
        
        protected, placeholders = protect_code_blocks(text)
        assert len(placeholders) == 1


# ============================================================================
# Test: Header Extraction
# ============================================================================

class TestHeaderExtraction:
    """헤더 추출 테스트"""
    
    def test_extract_single_level_headers(self):
        """단일 레벨 헤더 추출"""
        text = """# Header 1
content
# Header 2
more content"""
        
        headers = extract_header_marks(text)
        
        assert len(headers) == 2
        assert headers[0].title == "Header 1"
        assert headers[0].level == 1
        assert headers[1].title == "Header 2"
    
    def test_extract_nested_headers(self):
        """중첩 헤더의 경로(breadcrumb) 추적"""
        text = """# Section 1
## Subsection 1.1
### Deep 1.1.1
## Subsection 1.2
# Section 2"""
        
        headers = extract_header_marks(text)
        
        assert len(headers) == 5
        
        # Section 1
        assert headers[0].path == ["Section 1"]
        
        # Subsection 1.1
        assert headers[1].path == ["Section 1", "Subsection 1.1"]
        
        # Deep 1.1.1
        assert headers[2].path == ["Section 1", "Subsection 1.1", "Deep 1.1.1"]
        
        # Subsection 1.2 - 하위 레벨 초기화 확인
        assert headers[3].path == ["Section 1", "Subsection 1.2"]
        
        # Section 2 - 상위 레벨로 돌아감
        assert headers[4].path == ["Section 2"]
    
    def test_header_positions(self):
        """헤더 위치 정보"""
        text = "# First\nSome text\n## Second"
        headers = extract_header_marks(text)
        
        assert headers[0].position == 0
        assert headers[1].position > headers[0].position


# ============================================================================
# Test: Semantic Chunking
# ============================================================================

class TestSemanticChunking:
    """Semantic Chunking 테스트"""
    
    def test_basic_chunking(self):
        """기본 청킹 (## 레벨 기준)"""
        text = """# Main Title

## Section 1
Content for section 1.
This has some text here.

## Section 2
Content for section 2.
More content here.
"""
        chunks = semantic_chunk(text, source="test.md")
        
        # ## 레벨로 2개의 청크 생성 예상
        assert len(chunks) >= 2
        
        # 메타데이터 확인
        for chunk in chunks:
            assert chunk.metadata["source"] == "test.md"
            assert "header_path" in chunk.metadata
    
    def test_chunking_with_subsections(self):
        """하위 섹션 병합"""
        text = """## Parent Section
Intro text.

### Child 1
Child 1 content.

### Child 2
Child 2 content.
"""
        chunks = semantic_chunk(text, source="test.md")
        
        # 하위 섹션도 하나의 청크에 포함
        assert len(chunks) == 1
        assert "Child 1 content" in chunks[0].text
        assert "Child 2 content" in chunks[0].text
    
    def test_empty_sections_skipped(self):
        """빈 섹션 건너뛰기"""
        text = """## Empty Section

## Content Section
Actual content here.
"""
        chunks = semantic_chunk(text, source="test.md")
        
        # 빈 섹션은 건너뛰어야 함
        for chunk in chunks:
            assert len(chunk.text.strip()) > 0
    
    def test_frontmatter_included_in_metadata(self):
        """frontmatter가 메타데이터에 포함"""
        text = """---
tags:
  - test
  - demo
---
## Section
Content here.
"""
        chunks = semantic_chunk(text, source="test.md")
        
        assert len(chunks) >= 1
        assert "frontmatter" in chunks[0].metadata
        assert chunks[0].metadata["frontmatter"]["tags"] == ["test", "demo"]
    
    def test_code_blocks_preserved(self):
        """코드 블록이 분할되지 않고 보존"""
        text = """## Code Section
Here is some code:

```python
def very_long_function():
    # This is a long comment that should not cause the code block to split
    x = 1
    y = 2
    z = 3
    return x + y + z
```

Some text after.
"""
        chunks = semantic_chunk(text, source="test.md", max_size=100)
        
        # 코드 블록이 온전히 보존되어 있어야 함
        found_code = False
        for chunk in chunks:
            if "def very_long_function():" in chunk.text:
                found_code = True
                assert "return x + y + z" in chunk.text  # 코드가 분할되지 않음
        
        assert found_code, "Code block should be preserved in chunks"


# ============================================================================
# Test: File Processing
# ============================================================================

class TestFileProcessing:
    """파일 처리 테스트"""
    
    def test_process_real_file(self):
        """실제 마크다운 파일 처리"""
        test_file = project_root / "src" / "test" / "Transformer models.md"
        
        if test_file.exists():
            chunks = process_markdown_file(test_file)
            
            assert len(chunks) > 0
            
            # 첫 번째 청크의 메타데이터 확인
            first = chunks[0]
            assert first.metadata["source"] == "Transformer models.md"
            
            # frontmatter가 있어야 함
            assert "frontmatter" in first.metadata
            
            print(f"\n[테스트 결과] 총 {len(chunks)}개의 청크 생성")
            for i, chunk in enumerate(chunks[:3]):  # 처음 3개만 출력
                print(f"\n--- Chunk {i+1} ---")
                print(f"Header Path: {chunk.metadata.get('header_path', 'N/A')}")
                print(f"Text Preview: {chunk.text[:100]}...")
        else:
            pytest.skip("Test file not found")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # pytest로 실행하거나 직접 실행 가능
    pytest.main([__file__, "-v", "--tb=short"])
