"""SQLite 데이터베이스 모델"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid


class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # 기본 경로: ~/.config/focus-guardian/data.db
            config_dir = Path.home() / ".config" / "focus-guardian"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(config_dir / "data.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """데이터베이스 테이블 생성"""
        cursor = self.conn.cursor()

        # 사용자 설정
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                default_duration INTEGER DEFAULT 45,
                break_interval INTEGER DEFAULT 15,
                pomodoro_mode BOOLEAN DEFAULT 0,
                strict_mode BOOLEAN DEFAULT 0,
                notification_enabled BOOLEAN DEFAULT 1,
                notification_position TEXT DEFAULT 'top-right',
                notification_duration INTEGER DEFAULT 5,
                notification_sound BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 앱 카테고리
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT CHECK(type IN ('work', 'entertainment', 'neutral')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 앱 정의
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id TEXT,
                app_name TEXT NOT NULL,
                process_name TEXT,
                title_pattern TEXT,
                FOREIGN KEY (category_id) REFERENCES app_categories(id)
            )
        """)

        # 집중 세션
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id TEXT PRIMARY KEY,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                target_duration INTEGER NOT NULL,
                actual_duration INTEGER,
                app_name TEXT,
                category_id TEXT,
                switch_attempts INTEGER DEFAULT 0,
                switches_blocked INTEGER DEFAULT 0,
                switches_allowed INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES app_categories(id)
            )
        """)

        # 창 전환 이벤트
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS switch_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                from_app TEXT,
                to_app TEXT,
                blocked BOOLEAN,
                user_choice TEXT CHECK(user_choice IN ('continue', 'extend', 'switch', NULL)),
                FOREIGN KEY (session_id) REFERENCES focus_sessions(id)
            )
        """)

        # 일일 통계
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_focus_time INTEGER,
                sessions_completed INTEGER,
                sessions_abandoned INTEGER,
                distraction_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON focus_sessions(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_switch_events_session ON switch_events(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_switch_events_timestamp ON switch_events(timestamp)")

        # 기본 설정 삽입 (없는 경우)
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO settings (id) VALUES (1)")

        self.conn.commit()

    # === 설정 관련 메서드 ===
    def get_settings(self) -> dict:
        """현재 설정 가져오기"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM settings WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else {}

    def update_settings(self, **kwargs):
        """설정 업데이트"""
        allowed_fields = [
            'default_duration', 'break_interval', 'pomodoro_mode', 'strict_mode',
            'notification_enabled', 'notification_position', 'notification_duration',
            'notification_sound'
        ]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [datetime.now().isoformat()]

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE settings SET {set_clause}, updated_at = ? WHERE id = 1", values)
        self.conn.commit()

    # === 세션 관련 메서드 ===
    def create_session(self, target_duration: int, app_name: str = None, category_id: str = None) -> str:
        """새 집중 세션 생성"""
        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO focus_sessions (id, start_time, target_duration, app_name, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, datetime.now().isoformat(), target_duration, app_name, category_id))
        self.conn.commit()
        return session_id

    def end_session(self, session_id: str, completed: bool = False):
        """세션 종료"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT start_time FROM focus_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return

        start_time = datetime.fromisoformat(row['start_time'])
        actual_duration = int((datetime.now() - start_time).total_seconds() / 60)

        cursor.execute("""
            UPDATE focus_sessions
            SET end_time = ?, actual_duration = ?, completed = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), actual_duration, completed, session_id))
        self.conn.commit()

    def get_active_session(self) -> Optional[dict]:
        """현재 활성 세션 가져오기"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM focus_sessions
            WHERE end_time IS NULL
            ORDER BY start_time DESC LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

    def record_switch_attempt(self, session_id: str, from_app: str, to_app: str,
                               blocked: bool, user_choice: str = None):
        """창 전환 시도 기록"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO switch_events (session_id, from_app, to_app, blocked, user_choice)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, from_app, to_app, blocked, user_choice))

        # 세션 통계 업데이트
        if blocked:
            cursor.execute("""
                UPDATE focus_sessions
                SET switch_attempts = switch_attempts + 1, switches_blocked = switches_blocked + 1
                WHERE id = ?
            """, (session_id,))
        else:
            cursor.execute("""
                UPDATE focus_sessions
                SET switch_attempts = switch_attempts + 1, switches_allowed = switches_allowed + 1
                WHERE id = ?
            """, (session_id,))

        self.conn.commit()

    # === 통계 관련 메서드 ===
    def get_today_stats(self) -> dict:
        """오늘의 통계 가져오기"""
        today = datetime.now().date().isoformat()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COALESCE(SUM(actual_duration), 0) as total_focus_time,
                COUNT(CASE WHEN completed = 1 THEN 1 END) as sessions_completed,
                COUNT(CASE WHEN completed = 0 AND end_time IS NOT NULL THEN 1 END) as sessions_abandoned,
                COALESCE(SUM(switch_attempts), 0) as total_switch_attempts,
                COALESCE(SUM(switches_blocked), 0) as switches_blocked
            FROM focus_sessions
            WHERE date(start_time) = ?
        """, (today,))

        row = cursor.fetchone()
        return dict(row) if row else {
            'total_focus_time': 0,
            'sessions_completed': 0,
            'sessions_abandoned': 0,
            'total_switch_attempts': 0,
            'switches_blocked': 0
        }

    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()
