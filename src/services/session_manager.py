"""집중 세션 관리자"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable
from PySide6.QtCore import QObject, QTimer, Signal

from services.window_monitor import WindowMonitor, WindowInfo, AppClassifier
from services.notification import NotificationService
from models.database import Database


class FocusSession:
    """집중 세션 데이터"""

    def __init__(
        self,
        session_id: str,
        target_duration: int,  # 분
        app_name: str = None,
        category_id: str = None
    ):
        self.id = session_id
        self.target_duration = target_duration
        self.app_name = app_name
        self.category_id = category_id
        self.start_time = datetime.now()
        self.paused = False
        self.pause_start: Optional[datetime] = None
        self.total_paused_time = timedelta()

    @property
    def elapsed_seconds(self) -> int:
        """경과 시간 (초)"""
        elapsed = datetime.now() - self.start_time - self.total_paused_time
        if self.paused and self.pause_start:
            elapsed -= (datetime.now() - self.pause_start)
        return int(elapsed.total_seconds())

    @property
    def elapsed_minutes(self) -> int:
        """경과 시간 (분)"""
        return self.elapsed_seconds // 60

    @property
    def remaining_seconds(self) -> int:
        """남은 시간 (초)"""
        return max(0, self.target_duration * 60 - self.elapsed_seconds)

    @property
    def remaining_minutes(self) -> int:
        """남은 시간 (분)"""
        return self.remaining_seconds // 60

    @property
    def progress(self) -> float:
        """진행률 (0.0 ~ 1.0)"""
        if self.target_duration == 0:
            return 1.0
        return min(1.0, self.elapsed_seconds / (self.target_duration * 60))

    @property
    def is_completed(self) -> bool:
        """목표 시간 달성 여부"""
        return self.elapsed_minutes >= self.target_duration


class SessionManager(QObject):
    """집중 세션 관리자"""

    # 시그널
    session_started = Signal(FocusSession)
    session_ended = Signal(FocusSession, bool)  # (세션, 완료여부)
    session_updated = Signal(FocusSession)  # 매 분마다
    focus_interrupted = Signal(WindowInfo, WindowInfo)  # 집중 중 창 전환 시도

    def __init__(
        self,
        db: Database,
        window_monitor: WindowMonitor,
        app_classifier: AppClassifier,
        notification_service: NotificationService
    ):
        super().__init__()
        self.db = db
        self.window_monitor = window_monitor
        self.app_classifier = app_classifier
        self.notification_service = notification_service

        self._current_session: Optional[FocusSession] = None
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._on_timer_tick)

        # 마지막 작업 창 저장 (복귀용)
        self._last_work_window: Optional[WindowInfo] = None

        # 창 전환 이벤트 연결
        self.window_monitor.window_changed.connect(self._on_window_changed)

        # 설정 로드
        settings = self.db.get_settings()
        self.default_duration = settings.get('default_duration', 45)
        self.strict_mode = settings.get('strict_mode', False)

    @property
    def current_session(self) -> Optional[FocusSession]:
        return self._current_session

    @property
    def is_active(self) -> bool:
        return self._current_session is not None and not self._current_session.paused

    def start_session(self, duration: int = None, app_name: str = None) -> FocusSession:
        """새 집중 세션 시작"""
        if self._current_session:
            self.end_session(completed=False)

        duration = duration or self.default_duration

        # 현재 창 정보
        current_window = self.window_monitor.get_current_window()
        if current_window and not app_name:
            app_name = current_window.app_name
            category = self.app_classifier.classify(current_window)
            category_id = category['id']
        else:
            category_id = None

        # DB에 세션 생성
        session_id = self.db.create_session(
            target_duration=duration,
            app_name=app_name,
            category_id=category_id
        )

        # 세션 객체 생성
        self._current_session = FocusSession(
            session_id=session_id,
            target_duration=duration,
            app_name=app_name,
            category_id=category_id
        )

        # 타이머 시작 (1분마다 업데이트)
        self._update_timer.start(60000)

        self.session_started.emit(self._current_session)
        return self._current_session

    def end_session(self, completed: bool = None):
        """세션 종료"""
        if not self._current_session:
            return

        self._update_timer.stop()

        # 완료 여부 자동 판단
        if completed is None:
            completed = self._current_session.is_completed

        # DB 업데이트
        self.db.end_session(self._current_session.id, completed=completed)

        session = self._current_session
        self._current_session = None

        self.session_ended.emit(session, completed)

    def pause_session(self):
        """세션 일시정지"""
        if self._current_session and not self._current_session.paused:
            self._current_session.paused = True
            self._current_session.pause_start = datetime.now()
            self._update_timer.stop()

    def resume_session(self):
        """세션 재개"""
        if self._current_session and self._current_session.paused:
            if self._current_session.pause_start:
                pause_duration = datetime.now() - self._current_session.pause_start
                self._current_session.total_paused_time += pause_duration
            self._current_session.paused = False
            self._current_session.pause_start = None
            self._update_timer.start(60000)

    def extend_session(self, minutes: int = 5):
        """세션 시간 연장"""
        if self._current_session:
            self._current_session.target_duration += minutes
            self.session_updated.emit(self._current_session)

    def _on_timer_tick(self):
        """타이머 틱 (1분마다)"""
        if not self._current_session:
            return

        # 세션 완료 체크
        if self._current_session.is_completed:
            self.end_session(completed=True)
            return

        self.session_updated.emit(self._current_session)

    def _on_window_changed(self, old_window: WindowInfo, new_window: WindowInfo):
        """창 전환 이벤트 처리"""
        if not self._current_session or self._current_session.paused:
            return

        # Focus Guardian 앱 자체는 무시
        if 'focus' in new_window.app_name.lower() or 'python' in new_window.process_name.lower():
            return
        if 'Focus Guardian' in new_window.title:
            return

        old_category = self.app_classifier.classify(old_window)
        new_category = self.app_classifier.classify(new_window)

        # 작업 창이면 마지막 작업 창으로 저장
        if old_category['type'] == 'work':
            self._last_work_window = old_window

        # 오직 엔터테인먼트 앱으로 전환할 때만 알림
        # (작업 앱 간 전환, neutral 앱 전환은 허용)
        if new_category['type'] == 'entertainment':
            self._handle_distraction(old_window, new_window)

    def _handle_distraction(self, old_window: WindowInfo, new_window: WindowInfo):
        """방해 요소 처리 - 토스트 표시"""
        remaining = self._current_session.remaining_minutes

        # 복귀할 작업 창 결정 (마지막 작업 창 또는 이전 창)
        return_window = self._last_work_window or old_window

        def on_choice(choice: str):
            if choice == 'continue':
                # 창 전환 차단 기록
                self.db.record_switch_attempt(
                    session_id=self._current_session.id,
                    from_app=old_window.app_name,
                    to_app=new_window.app_name,
                    blocked=True,
                    user_choice='continue'
                )
                # 엔터테인먼트 탭 닫기
                self.window_monitor.close_tab(new_window.window_id)
                # 마지막 작업 창으로 자동 복귀
                if return_window:
                    self.window_monitor.activate_window(return_window.window_id)
            elif choice == 'extend':
                self.extend_session(5)
                self.db.record_switch_attempt(
                    session_id=self._current_session.id,
                    from_app=old_window.app_name,
                    to_app=new_window.app_name,
                    blocked=True,
                    user_choice='extend'
                )
                # 엔터테인먼트 탭 닫기
                self.window_monitor.close_tab(new_window.window_id)
                # 마지막 작업 창으로 자동 복귀
                if return_window:
                    self.window_monitor.activate_window(return_window.window_id)
            elif choice == 'switch':
                # 전환 허용
                self.db.record_switch_attempt(
                    session_id=self._current_session.id,
                    from_app=old_window.app_name,
                    to_app=new_window.app_name,
                    blocked=False,
                    user_choice='switch'
                )
                self.pause_session()

        self.notification_service.show_focus_reminder(
            remaining_minutes=remaining,
            on_choice=on_choice
        )

        self.focus_interrupted.emit(old_window, new_window)
