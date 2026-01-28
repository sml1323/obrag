from fastapi import APIRouter, Depends
from api.deps import get_syncer
from core.sync.incremental_syncer import IncrementalSyncer, SyncResult

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/trigger", response_model=SyncResult)
def trigger_sync(syncer: IncrementalSyncer = Depends(get_syncer)):
    """
    증분 동기화 트리거
    
    1. 변경된 파일을 감지하여 ChromaDB에 업데이트합니다.
    2. 동기화 결과를 반환합니다.
    
    이 작업은 I/O 바운드 작업이므로 스레드풀에서 실행됩니다 (def 라우터).
    """
    return syncer.sync()
