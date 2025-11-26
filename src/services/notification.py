"""토스트 팝업 알림 서비스"""
import random
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QPoint
from PySide6.QtGui import QFont, QColor


class ToastNotification(QWidget):
    """토스트 팝업 알림 위젯"""

    # 사용자 선택 시그널
    choice_made = Signal(str)  # 'continue', 'extend', 'switch'

    def __init__(
        self,
        message: str,
        remaining_minutes: int = 0,
        position: str = "top-right",
        duration: int = 0,  # 0이면 자동으로 닫히지 않음
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.message = message
        self.remaining_minutes = remaining_minutes
        self.position = position
        self.duration = duration

        self._setup_ui()
        self._setup_style()
        self._setup_animation()

    def _setup_ui(self):
        """UI 구성"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(380)

        # 메인 컨테이너
        container = QWidget()
        container.setObjectName("container")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 헤더
        header = QLabel("🎯 Focus Guardian")
        header.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #6366f1;")
        layout.addWidget(header)

        # 메시지
        msg_label = QLabel(self.message)
        msg_label.setFont(QFont("Sans", 12))
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #1f2937;")
        layout.addWidget(msg_label)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_continue = QPushButton("계속 집중")
        self.btn_continue.setObjectName("primaryBtn")
        self.btn_continue.clicked.connect(lambda: self._on_choice("continue"))

        self.btn_extend = QPushButton("5분만 더")
        self.btn_extend.setObjectName("secondaryBtn")
        self.btn_extend.clicked.connect(lambda: self._on_choice("extend"))

        self.btn_switch = QPushButton("전환하기")
        self.btn_switch.setObjectName("tertiaryBtn")
        self.btn_switch.clicked.connect(lambda: self._on_choice("switch"))

        btn_layout.addWidget(self.btn_continue)
        btn_layout.addWidget(self.btn_extend)
        btn_layout.addWidget(self.btn_switch)
        layout.addLayout(btn_layout)

        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)

    def _setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            #container {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }

            #primaryBtn {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            #primaryBtn:hover {
                background-color: #4f46e5;
            }

            #secondaryBtn {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
            }
            #secondaryBtn:hover {
                background-color: #e5e7eb;
            }

            #tertiaryBtn {
                background-color: transparent;
                color: #6b7280;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
            }
            #tertiaryBtn:hover {
                background-color: #f3f4f6;
                color: #374151;
            }
        """)

    def _setup_animation(self):
        """애니메이션 설정"""
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(200)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _on_choice(self, choice: str):
        """버튼 클릭 처리"""
        self.choice_made.emit(choice)
        self.close_with_animation()

    def show_at_position(self):
        """지정된 위치에 표시"""
        self.adjustSize()

        screen = QApplication.primaryScreen().availableGeometry()
        margin = 20

        if self.position == "top-right":
            x = screen.right() - self.width() - margin
            y = screen.top() + margin
        elif self.position == "top-left":
            x = screen.left() + margin
            y = screen.top() + margin
        elif self.position == "bottom-right":
            x = screen.right() - self.width() - margin
            y = screen.bottom() - self.height() - margin
        elif self.position == "bottom-left":
            x = screen.left() + margin
            y = screen.bottom() - self.height() - margin
        else:
            x = screen.right() - self.width() - margin
            y = screen.top() + margin

        self.move(x, y)
        self.setWindowOpacity(0)
        self.show()

        # 페이드 인
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.start()

        # 자동 닫기 타이머
        if self.duration > 0:
            QTimer.singleShot(self.duration * 1000, self.close_with_animation)

    def close_with_animation(self):
        """애니메이션과 함께 닫기"""
        self.fade_anim.setStartValue(1)
        self.fade_anim.setEndValue(0)
        self.fade_anim.finished.connect(self.close)
        self.fade_anim.start()


class NotificationService:
    """알림 서비스"""

    DEFAULT_MESSAGES = [
        "{n}분만 더 집중해볼까요? 🎯",
        "거의 다 왔어요! {n}분만 더 화이팅! 💪",
        "지금 전환하시겠어요? 목표까지 {n}분 남았습니다",
        "집중 중입니다. 정말 창을 전환하시겠습니까?"
    ]

    def __init__(
        self,
        position: str = "top-right",
        messages: list = None,
        sound_enabled: bool = True
    ):
        self.position = position
        self.messages = messages or self.DEFAULT_MESSAGES
        self.sound_enabled = sound_enabled
        self._current_toast: Optional[ToastNotification] = None

    def show_focus_reminder(
        self,
        remaining_minutes: int,
        on_choice: Callable[[str], None] = None
    ) -> ToastNotification:
        """
        집중 리마인더 토스트 표시

        Args:
            remaining_minutes: 남은 시간 (분)
            on_choice: 사용자 선택 콜백 ('continue', 'extend', 'switch')
        """
        # 이전 토스트 닫기
        if self._current_toast:
            self._current_toast.close()

        # 메시지 선택 및 포맷팅
        message = random.choice(self.messages)
        message = message.replace("{n}", str(remaining_minutes))

        # 토스트 생성
        toast = ToastNotification(
            message=message,
            remaining_minutes=remaining_minutes,
            position=self.position
        )

        if on_choice:
            toast.choice_made.connect(on_choice)

        self._current_toast = toast
        toast.show_at_position()

        return toast

    def close_current(self):
        """현재 토스트 닫기"""
        if self._current_toast:
            self._current_toast.close_with_animation()
            self._current_toast = None
