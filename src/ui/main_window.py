"""메인 윈도우 UI"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame,
    QSpinBox, QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont, QIcon, QAction

from services.session_manager import SessionManager, FocusSession


class StatsCard(QFrame):
    """통계 카드 위젯"""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statsCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #6b7280; font-size: 12px;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #1f2937; font-size: 18px; font-weight: bold;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    """메인 윈도우"""

    def __init__(self, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager

        self._setup_ui()
        self._setup_tray()
        self._connect_signals()
        self._update_stats()

        # UI 업데이트 타이머 (1초마다)
        self._ui_timer = QTimer()
        self._ui_timer.timeout.connect(self._update_ui)
        self._ui_timer.start(1000)

    def _setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("Focus Guardian")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)

        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 헤더
        header = QLabel("🎯 Focus Guardian")
        header.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # 상태 표시
        self.status_label = QLabel("준비됨")
        self.status_label.setStyleSheet("color: #6b7280; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 타이머 표시
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Sans", 48, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #1f2937;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e5e7eb;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 시간 설정
        time_layout = QHBoxLayout()
        time_layout.addStretch()

        time_label = QLabel("집중 시간:")
        time_label.setStyleSheet("color: #6b7280;")
        time_layout.addWidget(time_label)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 180)
        self.duration_spin.setValue(45)
        self.duration_spin.setSuffix(" 분")
        self.duration_spin.setFixedWidth(100)
        time_layout.addWidget(self.duration_spin)

        time_layout.addStretch()
        layout.addLayout(time_layout)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.start_btn = QPushButton("세션 시작")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.setFixedHeight(44)
        self.start_btn.clicked.connect(self._on_start_clicked)

        self.pause_btn = QPushButton("일시정지")
        self.pause_btn.setObjectName("secondaryBtn")
        self.pause_btn.setFixedHeight(44)
        self.pause_btn.setVisible(False)
        self.pause_btn.clicked.connect(self._on_pause_clicked)

        self.stop_btn = QPushButton("종료")
        self.stop_btn.setObjectName("tertiaryBtn")
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #e5e7eb;")
        layout.addWidget(line)

        # 오늘의 통계
        stats_header = QLabel("📊 오늘의 통계")
        stats_header.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        layout.addWidget(stats_header)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.total_time_card = StatsCard("총 집중 시간", "0분")
        self.sessions_card = StatsCard("완료 세션", "0개")
        self.defense_card = StatsCard("방어 성공", "0/0")

        stats_layout.addWidget(self.total_time_card)
        stats_layout.addWidget(self.sessions_card)
        stats_layout.addWidget(self.defense_card)
        layout.addLayout(stats_layout)

        layout.addStretch()

        # 스타일 적용
        self._apply_styles()

    def _apply_styles(self):
        """전체 스타일 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }

            #statsCard {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #primaryBtn {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            #primaryBtn:hover {
                background-color: #4f46e5;
            }
            #primaryBtn:disabled {
                background-color: #9ca3af;
            }

            #secondaryBtn {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
            }
            #secondaryBtn:hover {
                background-color: #e5e7eb;
            }

            #tertiaryBtn {
                background-color: transparent;
                color: #ef4444;
                border: 1px solid #ef4444;
                border-radius: 8px;
                font-size: 14px;
            }
            #tertiaryBtn:hover {
                background-color: #fef2f2;
            }

            QSpinBox {
                padding: 8px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: white;
            }
        """)

    def _setup_tray(self):
        """시스템 트레이 설정"""
        self.tray_icon = QSystemTrayIcon(self)
        # 기본 아이콘 사용 (실제로는 아이콘 파일 필요)
        self.tray_icon.setToolTip("Focus Guardian")

        # 트레이 메뉴
        tray_menu = QMenu()

        show_action = QAction("열기", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("종료", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _connect_signals(self):
        """시그널 연결"""
        self.session_manager.session_started.connect(self._on_session_started)
        self.session_manager.session_ended.connect(self._on_session_ended)
        self.session_manager.session_updated.connect(self._on_session_updated)

    def _on_tray_activated(self, reason):
        """트레이 아이콘 클릭"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    @Slot()
    def _on_start_clicked(self):
        """세션 시작 버튼"""
        duration = self.duration_spin.value()
        self.session_manager.start_session(duration=duration)

    @Slot()
    def _on_pause_clicked(self):
        """일시정지/재개 버튼"""
        session = self.session_manager.current_session
        if session:
            if session.paused:
                self.session_manager.resume_session()
                self.pause_btn.setText("일시정지")
            else:
                self.session_manager.pause_session()
                self.pause_btn.setText("재개")

    @Slot()
    def _on_stop_clicked(self):
        """종료 버튼"""
        self.session_manager.end_session(completed=False)

    @Slot(FocusSession)
    def _on_session_started(self, session: FocusSession):
        """세션 시작됨"""
        self.start_btn.setVisible(False)
        self.pause_btn.setVisible(True)
        self.stop_btn.setVisible(True)
        self.duration_spin.setEnabled(False)
        self.status_label.setText("🎯 집중 중")
        self.status_label.setStyleSheet("color: #6366f1; font-size: 14px;")

    @Slot(FocusSession, bool)
    def _on_session_ended(self, session: FocusSession, completed: bool):
        """세션 종료됨"""
        self.start_btn.setVisible(True)
        self.pause_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.duration_spin.setEnabled(True)
        self.progress_bar.setValue(0)
        self.timer_label.setText("00:00")

        if completed:
            self.status_label.setText("✅ 목표 달성!")
            self.status_label.setStyleSheet("color: #10b981; font-size: 14px;")
        else:
            self.status_label.setText("준비됨")
            self.status_label.setStyleSheet("color: #6b7280; font-size: 14px;")

        self._update_stats()

    @Slot(FocusSession)
    def _on_session_updated(self, session: FocusSession):
        """세션 업데이트"""
        self._update_ui()

    def _update_ui(self):
        """UI 업데이트"""
        session = self.session_manager.current_session
        if not session:
            return

        # 타이머 표시 (남은 시간을 초 단위로 계산)
        remaining_secs = session.remaining_seconds
        minutes = remaining_secs // 60
        seconds = remaining_secs % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

        # 프로그레스 바
        self.progress_bar.setValue(int(session.progress * 100))

        # 상태
        if session.paused:
            self.status_label.setText("⏸️ 일시정지")
            self.status_label.setStyleSheet("color: #f59e0b; font-size: 14px;")

    def _update_stats(self):
        """통계 업데이트"""
        stats = self.session_manager.db.get_today_stats()

        # 총 집중 시간
        total_minutes = stats.get('total_focus_time', 0)
        if total_minutes >= 60:
            hours = total_minutes // 60
            mins = total_minutes % 60
            self.total_time_card.set_value(f"{hours}시간 {mins}분")
        else:
            self.total_time_card.set_value(f"{total_minutes}분")

        # 완료 세션
        completed = stats.get('sessions_completed', 0)
        self.sessions_card.set_value(f"{completed}개")

        # 방어 성공
        blocked = stats.get('switches_blocked', 0)
        total = stats.get('total_switch_attempts', 0)
        self.defense_card.set_value(f"{blocked}/{total}")

    def closeEvent(self, event):
        """창 닫기 이벤트 - 트레이로 최소화"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Focus Guardian",
            "백그라운드에서 실행 중입니다.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
