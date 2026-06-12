"""
phase2 테스트 공통 픽스처.

deps 모듈의 embedder/store/llm 캐시는 프로세스 전역(module-level)이므로,
테스트 간 인스턴스가 공유되면 mock 기반 wiring 테스트의 격리가 깨진다.
각 테스트 전후로 캐시를 비워 격리를 보장한다.
"""

import sys
from pathlib import Path

# src/ 를 import 경로에 추가 (개별 테스트 파일의 bootstrap과 동일)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


@pytest.fixture(autouse=True)
def _reset_deps_caches():
    from api import deps

    deps.reset_resource_caches()
    yield
    deps.reset_resource_caches()
