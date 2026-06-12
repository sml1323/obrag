import ipaddress
import socket
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.deps import get_session
from core.domain.settings import Settings
from api.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _validate_vault_path(path: str | None) -> None:
    """vault_path 가 실제 존재하는 디렉터리인지 검증 (오타/임의경로 방지)."""
    if not path:
        return
    if not Path(path).expanduser().is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"vault_path is not an existing directory: {path}",
        )


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    """링크로컬(메타데이터)·멀티캐스트·예약·미지정 주소는 차단.

    loopback(127.0.0.1, ::1)은 로컬 ollama 의 정상 경로이므로 허용한다.
    (참고: IPv6 loopback ::1 은 ipaddress 에서 is_reserved=True 이므로 명시 예외)
    """
    if ip.is_loopback:
        return False
    return bool(
        ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified
    )


def _validate_ollama_endpoint(url: str | None) -> None:
    """
    ollama_endpoint 의 SSRF 표면 차단.

    사용자가 임의 URL 을 설정하면 서버가 그 주소로 요청을 보내므로,
    스킴(http/https) 과 클라우드 메타데이터/링크로컬 주소를 거부한다.
    localhost/사설망/일반 호스트명은 정상 사용을 위해 허용한다.

    인코딩된 IPv4(십진/16진/8진: http://2852039166/, http://0xA9FEA9FE/ 등)와
    내부 IP 로 resolve 되는 DNS 이름까지 막기 위해, 리터럴 파싱 + inet_aton +
    getaddrinfo 로 후보 주소를 모두 모아 deny-list 를 적용한다.
    (resolve 실패 호스트는 정상 UX 를 위해 허용 — request-time 가 아닌 save-time 검증)
    """
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400, detail="ollama_endpoint must be an http(s) URL"
        )
    host = parsed.hostname or ""
    if host.lower() in {"metadata.google.internal", "metadata"}:
        raise HTTPException(
            status_code=400, detail="ollama_endpoint host is not allowed"
        )

    candidates: set[ipaddress._BaseAddress] = set()
    # 1) 리터럴 IP (점표기 IPv4 / IPv6)
    try:
        candidates.add(ipaddress.ip_address(host))
    except ValueError:
        pass
    # 2) 인코딩된 IPv4 (십진/16진/8진/부분표기) — inet_aton 이 정규화
    try:
        candidates.add(ipaddress.ip_address(socket.inet_ntoa(socket.inet_aton(host))))
    except OSError:
        pass
    # 3) DNS 이름 resolve (best-effort; 실패 시 허용)
    try:
        for info in socket.getaddrinfo(host, parsed.port or None):
            candidates.add(ipaddress.ip_address(info[4][0]))
    except (OSError, UnicodeError, ValueError):
        pass

    if any(_is_blocked_ip(ip) for ip in candidates):
        raise HTTPException(
            status_code=400,
            detail="ollama_endpoint points to a disallowed address range",
        )


@router.get("/", response_model=SettingsResponse)
def get_settings(session: Session = Depends(get_session)):
    settings = session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1)
        session.add(settings)
        session.commit()
        session.refresh(settings)

    return settings.mask_api_keys()


def _is_masked_value(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith("***") or value == "***"


@router.put("/", response_model=SettingsResponse)
def update_settings(
    settings_in: SettingsUpdate, session: Session = Depends(get_session)
):
    settings = session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1)

    update_data = settings_in.model_dump(exclude_unset=True)

    # 보안 검증 (네트워크 노출 시 path-traversal/SSRF 표면 축소)
    if "vault_path" in update_data:
        _validate_vault_path(update_data["vault_path"])
    if "ollama_endpoint" in update_data:
        _validate_ollama_endpoint(update_data["ollama_endpoint"])

    api_key_fields = {"llm_api_key", "embedding_api_key"}
    for key, value in update_data.items():
        if key in api_key_fields and _is_masked_value(value):
            continue
        setattr(settings, key, value)

    settings.updated_at = datetime.now(timezone.utc)

    session.add(settings)
    session.commit()
    session.refresh(settings)

    return settings.mask_api_keys()
