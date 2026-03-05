import sqlite3
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool

from src.utils.exception import he

DB_PATH = Path("memory/memory.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT NOT NULL,        -- 'user' hoặc 'assistant'
                content   TEXT NOT NULL,        -- nội dung tin nhắn
                timestamp TEXT NOT NULL         -- thời gian lưu
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,        -- tên công việc
                status    TEXT DEFAULT 'todo',  -- todo / doing / done
                timestamp TEXT NOT NULL         -- thời gian tạo
            )
        """)

        conn.commit()


init_db()


@tool
@he
def memory_save_conversation(role: str, content: str) -> str:
    """
    Lưu một tin nhắn vào lịch sử hội thoại.
    Dùng sau mỗi lượt trao đổi để agent nhớ được ngữ cảnh.
    Input:
      - role: 'user' hoặc 'assistant'
      - content: nội dung tin nhắn
    """

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, datetime.now().isoformat()),
        )

        conn.commit()

    return f"Đã lưu tin nhắn của '{role}'"


@tool
@he
def memory_get_conversations(limit: int = 10) -> str:
    """
    Lấy lịch sử hội thoại gần nhất.
    Dùng khi cần nhớ lại ngữ cảnh cuộc trò chuyện trước.
    Input: số lượng tin nhắn muốn lấy (mặc định 10)
    """

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    if not rows:
        return "Chưa có lịch sử hội thoại nào."

    rows = reversed(rows)

    result = "\n".join(f"[{ts[:16]}] {role}: {content}" for role, content, ts in rows)

    return result


@tool
@he
def memory_clear_conversations() -> str:
    """
    Xóa toàn bộ lịch sử hội thoại.
    Dùng khi muốn bắt đầu cuộc trò chuyện mới hoàn toàn.
    Không thể hoàn tác.
    """

    with get_connection() as conn:
        conn.execute("DELETE FROM conversations")

        conn.commit()

    return "Đã xóa toàn bộ lịch sử hội thoại."


@tool
@he
def memory_add_task(title: str) -> str:
    """
    Thêm một công việc mới vào danh sách.
    Trạng thái mặc định là 'todo'.
    Input: tên công việc cần làm
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, status, timestamp) VALUES (?, 'todo', ?)",
            (title, datetime.now().isoformat()),
        )
        conn.commit()
        task_id = cursor.lastrowid
    return f"Đã thêm task #{task_id}: '{title}' [todo]"


@tool
@he
def memory_get_tasks(status: str = "all") -> str:
    """
    Xem danh sách công việc.
    Input: trạng thái muốn lọc — 'all', 'todo', 'doing', 'done'
    """
    with get_connection() as conn:
        if status == "all":
            rows = conn.execute(
                "SELECT id, title, status, timestamp FROM tasks ORDER BY id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, title, status, timestamp FROM tasks WHERE status = ? ORDER BY id",
                (status,),
            ).fetchall()

    if not rows:
        return f"Không có task nào với trạng thái '{status}'."

    result = "\n".join(
        f"#{id} [{status}] {title} — {ts[:10]}" for id, title, status, ts in rows
    )
    return result


@tool
@he
def memory_update_task(task_id: int, status: str) -> str:
    """
    Cập nhật trạng thái của một công việc.
    Input:
      - task_id: ID của task (lấy từ memory_get_tasks)
      - status: trạng thái mới — 'todo', 'doing', hoặc 'done'
    """
    valid = ["todo", "doing", "done"]
    if status not in valid:
        return f"Trạng thái không hợp lệ. Chỉ dùng: {valid}"

    with get_connection() as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()
    return f"Đã cập nhật task #{task_id} → [{status}]"


memory_tools = [
    memory_save_conversation,
    memory_get_conversations,
    memory_clear_conversations,
    memory_add_task,
    memory_get_tasks,
    memory_update_task,
]
