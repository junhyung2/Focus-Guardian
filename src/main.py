#!/usr/bin/env python3
"""Focus Guardian - 집중력 향상 데스크톱 애플리케이션"""
import sys
import json
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from models.database import Database
from services.window_monitor import WindowMonitor, AppClassifier
from services.notification import NotificationService
from services.session_manager import SessionManager
from ui.main_window import MainWindow


def load_config() -> dict:
    """설정 파일 로드"""
    # 사용자 설정 경로
    user_config = Path.home() / ".config" / "focus-guardian" / "settings.json"

    # 기본 설정 경로
    default_config = Path(__file__).parent.parent / "config" / "default_settings.json"

    config = {}

    # 기본 설정 로드
    if default_config.exists():
        with open(default_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

    # 사용자 설정으로 덮어쓰기
    if user_config.exists():
        with open(user_config, 'r', encoding='utf-8') as f:
            user_settings = json.load(f)
            config.update(user_settings)

    return config


def main():
    # 고DPI 지원
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Focus Guardian")
    app.setApplicationDisplayName("Focus Guardian")
    app.setQuitOnLastWindowClosed(False)  # 트레이로 최소화 허용

    # 설정 로드
    config = load_config()

    # 데이터베이스 초기화
    db = Database()

    # 서비스 초기화
    window_monitor = WindowMonitor(poll_interval=500)

    app_classifier = AppClassifier(
        categories=config.get('categories', [])
    )

    notification_config = config.get('notification', {})
    notification_service = NotificationService(
        position=notification_config.get('position', 'top-right'),
        messages=notification_config.get('messages'),
        sound_enabled=notification_config.get('sound', True)
    )

    session_manager = SessionManager(
        db=db,
        window_monitor=window_monitor,
        app_classifier=app_classifier,
        notification_service=notification_service
    )

    # 창 모니터링 시작
    window_monitor.start()

    # 메인 윈도우 생성
    main_window = MainWindow(session_manager=session_manager)
    main_window.show()

    # 앱 실행
    exit_code = app.exec()

    # 정리
    window_monitor.stop()
    db.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
