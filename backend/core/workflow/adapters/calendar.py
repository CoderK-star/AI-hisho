from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.config.loader import load_settings
from backend.core.workflow.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[4]

_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False


class GoogleCalendarAdapter(BaseAdapter):
    def __init__(self, config: dict[str, Any]) -> None:
        if not _GOOGLE_AVAILABLE:
            raise RuntimeError(
                "カレンダー連携には google-api-python-client 等が必要です。"
                "pip install -e '.[calendar]' でインストールしてください。"
            )
        self._credentials_path = _PROJECT_ROOT / config.get(
            "credentials_path", "data/calendar_credentials.json"
        )
        self._token_path = _PROJECT_ROOT / config.get(
            "token_path", "data/calendar_token.json"
        )
        self._service: Any = None

    @property
    def name(self) -> str:
        return "google_calendar"

    async def execute(self, **kwargs: Any) -> Any:
        return await self.get_upcoming_events(**kwargs)

    def _get_credentials(self) -> Any:
        creds = None
        if self._token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_path), _SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._credentials_path.exists():
                    raise FileNotFoundError(
                        f"Google Calendar の認証情報が見つかりません: {self._credentials_path}\n"
                        "Google Cloud Console で OAuth2 クライアント ID を作成し、"
                        "credentials.json をこのパスに配置してください。"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self._credentials_path), _SCOPES
                )
                creds = flow.run_local_server(port=0)

            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            self._token_path.write_text(creds.to_json())

        return creds

    def _get_service(self) -> Any:
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("calendar", "v3", credentials=creds)
        return self._service

    async def get_upcoming_events(
        self, days: int = 7, max_results: int = 20
    ) -> list[dict[str, Any]]:
        try:
            service = self._get_service()
        except FileNotFoundError as e:
            logger.error("Calendar: %s", e)
            return []

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=days)).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        items = events_result.get("items", [])

        return [_normalize_event(e) for e in items]

    async def health_check(self) -> bool:
        try:
            self._get_credentials()
            return True
        except Exception:
            return False


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    start = event.get("start", {})
    end = event.get("end", {})
    return {
        "id": event.get("id", ""),
        "title": event.get("summary", "(タイトルなし)"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": start.get("dateTime") or start.get("date", ""),
        "end": end.get("dateTime") or end.get("date", ""),
        "all_day": "date" in start and "dateTime" not in start,
        "url": event.get("htmlLink", ""),
    }


_adapter_instance: GoogleCalendarAdapter | None = None


def get_calendar_adapter() -> GoogleCalendarAdapter | None:
    global _adapter_instance
    if not _GOOGLE_AVAILABLE:
        return None

    cfg = load_settings().get("calendar", {})
    if not cfg.get("enabled", False):
        return None

    if _adapter_instance is None:
        _adapter_instance = GoogleCalendarAdapter(cfg)

    return _adapter_instance
