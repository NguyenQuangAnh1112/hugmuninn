import calendar
from calendar import Calendar
from datetime import datetime

from googleapiclient.discovery import build
from langchain_core.tools import tool

from src.utils.auth import get_credentials
from src.utils.exception import he


def get_calendar_service():
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)


@tool
@he
def list_events(max_results: int = 10) -> str:
    """Lấy danh sách sự kiện sắp tới trong Google Calendar."""

    service = get_calendar_service()

    now = datetime.utcnow().isoformat() + "Z"

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])
    if not events:
        return "Không có sự kiện nào sắp tới."

    result = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        result.append(f"- {e['summary']} | {start} | id: {e['id']}")

    return "\n".join(result)


@tool
@he
def create_event(
    summary: str, start_time: str, end_time: str, description: str = ""
) -> str:
    """
    Tạo sự kiện mới trong Google Calendar.
    - summary: tên sự kiện
    - start_time: thời gian bắt đầu (ISO format: 2025-03-05T09:00:00)
    - end_time: thời gian kết thúc (ISO format: 2025-03-05T10:00:00)
    - description: mô tả (tuỳ chọn)
    """

    service = get_calendar_service()

    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Ho_Chi_Minh"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Ho_Chi_Minh"},
    }

    result = service.events().insert(calendarId="primary", body=event).execute()
    return f"Đã tạo: {result.get('summary')} — {result.get('htmlLink')}"


@tool
@he
def update_event(
    event_id: str, summary: str = None, start_time: str = None, end_time: str = None
) -> str:
    """
    Cập nhật sự kiện đã có.
    - event_id: lấy từ list_events
    """

    service = get_calendar_service()

    event = service.events().get(calendarId="primary", eventId=event_id).execute()

    if summary:
        event["summary"] = summary
    if start_time:
        event["start"] = {"datetime": start_time, "timeZone": "Asia/Ho_Chi_Minh"}
    if end_time:
        event["end"] = {"dateTime": end_time, "timeZone": "Asia/Ho_Chi_Minh"}

    updated = (
        service.events()
        .update(calendarId="primary", eventId=event_id, body=event)
        .execute()
    )
    return f"Đã cập nhật: {updated.get('summary')}"


@tool
@he
def delete_event(event_id: str) -> str:
    """
    Xóa sự kiện khỏi Google Calendar.
    - event_id: lấy từ list_events
    """

    service = get_calendar_service()

    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"Đã xóa event id: {event_id}"
