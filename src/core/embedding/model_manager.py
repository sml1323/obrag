import os
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, TypedDict


class ModelStatus(str, Enum):
    NOT_FOUND = "not_found"
    DOWNLOADING = "downloading"
    READY = "ready"
    ERROR = "error"


@dataclass
class ModelInfo:
    model_id: str
    status: ModelStatus
    progress: float = 0.0
    size_mb: int | None = None
    error: str | None = None
    local_path: str | None = None


@dataclass
class DownloadProgress:
    model_id: str
    progress: float = 0.0
    status: ModelStatus = ModelStatus.DOWNLOADING
    error: str | None = None


_download_states: dict[str, DownloadProgress] = {}
_download_lock = threading.Lock()


class KnownModelInfo(TypedDict, total=False):
    size_mb: int
    dimension: int


class AvailableModelInfo(TypedDict):
    model_id: str
    size_mb: int | None
    dimension: int | None
    status: str
    is_cached: bool


KNOWN_MODELS: dict[str, KnownModelInfo] = {
    "BAAI/bge-m3": {"size_mb": 2200, "dimension": 1024},
    "dragonkue/BGE-m3-ko": {"size_mb": 2200, "dimension": 1024},
    "intfloat/multilingual-e5-large-instruct": {"size_mb": 2200, "dimension": 1024},
    "intfloat/multilingual-e5-large": {"size_mb": 2200, "dimension": 1024},
    "intfloat/multilingual-e5-base": {"size_mb": 1100, "dimension": 768},
    "intfloat/multilingual-e5-small": {"size_mb": 500, "dimension": 384},
}


def get_hf_cache_dir() -> Path:
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home) / "hub"

    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "huggingface" / "hub"

    return Path.home() / ".cache" / "huggingface" / "hub"


def model_id_to_cache_name(model_id: str) -> str:
    return "models--" + model_id.replace("/", "--")


def is_model_cached(model_id: str) -> bool:
    cache_dir = get_hf_cache_dir()
    model_cache_dir = cache_dir / model_id_to_cache_name(model_id)

    if not model_cache_dir.exists():
        return False

    snapshots_dir = model_cache_dir / "snapshots"
    if not snapshots_dir.exists():
        return False

    snapshot_dirs = list(snapshots_dir.iterdir())
    if not snapshot_dirs:
        return False

    for snapshot_dir in snapshot_dirs:
        if snapshot_dir.is_dir():
            model_files = (
                list(snapshot_dir.glob("*.safetensors"))
                + list(snapshot_dir.glob("*.bin"))
                + list(snapshot_dir.glob("pytorch_model*"))
            )
            if model_files:
                return True

    return False


def get_model_local_path(model_id: str) -> str | None:
    cache_dir = get_hf_cache_dir()
    model_cache_dir = cache_dir / model_id_to_cache_name(model_id)

    if not model_cache_dir.exists():
        return None

    snapshots_dir = model_cache_dir / "snapshots"
    if not snapshots_dir.exists():
        return None

    for snapshot_dir in sorted(snapshots_dir.iterdir(), reverse=True):
        if snapshot_dir.is_dir():
            return str(snapshot_dir)

    return None


def _get_blobs_dir_size(model_id: str) -> int:
    """Get total size of all files in the blobs directory (includes .incomplete)."""
    cache_dir = get_hf_cache_dir()
    blobs_dir = cache_dir / model_id_to_cache_name(model_id) / "blobs"
    if not blobs_dir.exists():
        return 0
    total = 0
    try:
        for f in blobs_dir.iterdir():
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def _get_expected_size_bytes(model_id: str) -> int:
    """Get expected total download size in bytes."""
    model_metadata = KNOWN_MODELS.get(model_id)
    if model_metadata and "size_mb" in model_metadata:
        return model_metadata["size_mb"] * 1024 * 1024

    try:
        from huggingface_hub import snapshot_download

        files = snapshot_download(model_id, dry_run=True)
        if isinstance(files, list):
            return sum(f.file_size for f in files)
    except Exception:
        pass
    return 0


def _monitor_download_progress(
    model_id: str,
    expected_size_bytes: int,
    stop_event: threading.Event,
) -> None:
    """Monitor blobs directory size and update download progress (0-90%)."""
    while not stop_event.is_set():
        current_size = _get_blobs_dir_size(model_id)
        if expected_size_bytes > 0:
            raw = current_size / expected_size_bytes
            progress = min(round(raw * 90.0, 1), 90.0)
        else:
            progress = 0.0

        with _download_lock:
            if model_id in _download_states:
                _download_states[model_id].progress = progress

        stop_event.wait(1.0)


def get_model_info(model_id: str) -> ModelInfo:
    model_metadata = KNOWN_MODELS.get(model_id)
    size_mb = model_metadata.get("size_mb") if model_metadata else None
    with _download_lock:
        if model_id in _download_states:
            state = _download_states[model_id]
            return ModelInfo(
                model_id=model_id,
                status=state.status,
                progress=state.progress,
                size_mb=size_mb,
                error=state.error,
            )

    if is_model_cached(model_id):
        return ModelInfo(
            model_id=model_id,
            status=ModelStatus.READY,
            progress=100.0,
            size_mb=size_mb,
            local_path=get_model_local_path(model_id),
        )

    return ModelInfo(
        model_id=model_id,
        status=ModelStatus.NOT_FOUND,
        progress=0.0,
        size_mb=size_mb,
    )


def download_model(
    model_id: str,
    on_progress: Callable[[float], None] | None = None,
) -> ModelInfo:
    with _download_lock:
        if model_id in _download_states:
            state = _download_states[model_id]
            if state.status == ModelStatus.DOWNLOADING:
                return ModelInfo(
                    model_id=model_id,
                    status=ModelStatus.DOWNLOADING,
                    progress=state.progress,
                )

        _download_states[model_id] = DownloadProgress(
            model_id=model_id,
            progress=0.0,
            status=ModelStatus.DOWNLOADING,
        )

    def update_progress(progress: float) -> None:
        with _download_lock:
            if model_id in _download_states:
                _download_states[model_id].progress = progress
        if on_progress:
            on_progress(progress)

    try:
        from huggingface_hub import snapshot_download
        from sentence_transformers import SentenceTransformer

        expected_size = _get_expected_size_bytes(model_id)

        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=_monitor_download_progress,
            args=(model_id, expected_size, stop_event),
            daemon=True,
        )
        monitor_thread.start()

        try:
            snapshot_download(model_id)
        finally:
            stop_event.set()
            monitor_thread.join(timeout=5.0)

        update_progress(90.0)

        _ = SentenceTransformer(model_id)

        update_progress(100.0)

        with _download_lock:
            if model_id in _download_states:
                _download_states[model_id].status = ModelStatus.READY
                _download_states[model_id].progress = 100.0

        model_metadata = KNOWN_MODELS.get(model_id)
        size_mb = model_metadata.get("size_mb") if model_metadata else None
        return ModelInfo(
            model_id=model_id,
            status=ModelStatus.READY,
            progress=100.0,
            size_mb=size_mb,
            local_path=get_model_local_path(model_id),
        )

    except Exception as e:
        error_msg = str(e)
        with _download_lock:
            if model_id in _download_states:
                _download_states[model_id].status = ModelStatus.ERROR
                _download_states[model_id].error = error_msg

        return ModelInfo(
            model_id=model_id,
            status=ModelStatus.ERROR,
            error=error_msg,
        )


def download_model_async(model_id: str) -> None:
    thread = threading.Thread(
        target=download_model,
        args=(model_id,),
        daemon=True,
    )
    thread.start()


def clear_download_state(model_id: str) -> None:
    with _download_lock:
        if model_id in _download_states:
            del _download_states[model_id]


def list_available_models() -> list[AvailableModelInfo]:
    models: list[AvailableModelInfo] = []
    for model_id, info in KNOWN_MODELS.items():
        model_info = get_model_info(model_id)
        models.append(
            {
                "model_id": model_id,
                "size_mb": info.get("size_mb"),
                "dimension": info.get("dimension"),
                "status": model_info.status.value,
                "is_cached": model_info.status == ModelStatus.READY,
            }
        )
    return models
