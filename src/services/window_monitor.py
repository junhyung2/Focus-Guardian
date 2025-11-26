"""창 모니터링 서비스 - Linux X11 환경"""
import re
import subprocess
from dataclasses import dataclass
from typing import Optional, Callable, List
from PySide6.QtCore import QObject, QTimer, Signal


@dataclass
class WindowInfo:
    """활성 창 정보"""
    window_id: str
    title: str
    app_name: str
    process_name: str


class WindowMonitor(QObject):
    """활성 창 모니터링 서비스"""

    # 시그널: 창이 변경되었을 때 발생
    window_changed = Signal(WindowInfo, WindowInfo)  # (이전 창, 새 창)

    def __init__(self, poll_interval: int = 500):
        """
        Args:
            poll_interval: 폴링 간격 (밀리초)
        """
        super().__init__()
        self.poll_interval = poll_interval
        self._timer = QTimer()
        self._timer.timeout.connect(self._check_active_window)
        self._current_window: Optional[WindowInfo] = None
        self._running = False

    def start(self):
        """모니터링 시작"""
        if self._running:
            return
        self._running = True
        self._current_window = self._get_active_window()
        self._timer.start(self.poll_interval)

    def stop(self):
        """모니터링 중지"""
        self._running = False
        self._timer.stop()

    def _check_active_window(self):
        """활성 창 확인 및 변경 감지"""
        new_window = self._get_active_window()

        if new_window is None:
            return

        if self._current_window is None:
            self._current_window = new_window
            return

        # 창이 변경되었는지 확인 (window_id 또는 title 기반)
        if (new_window.window_id != self._current_window.window_id or
            new_window.title != self._current_window.title):
            old_window = self._current_window
            self._current_window = new_window
            self.window_changed.emit(old_window, new_window)

    def _get_active_window(self) -> Optional[WindowInfo]:
        """현재 활성 창 정보 가져오기 (xdotool 사용)"""
        try:
            # 활성 창 ID 가져오기
            window_id = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True, text=True, timeout=1
            ).stdout.strip()

            if not window_id:
                return None

            # 창 제목 가져오기
            title = subprocess.run(
                ['xdotool', 'getwindowname', window_id],
                capture_output=True, text=True, timeout=1
            ).stdout.strip()

            # 창의 PID 가져오기
            pid_result = subprocess.run(
                ['xdotool', 'getwindowpid', window_id],
                capture_output=True, text=True, timeout=1
            )
            pid = pid_result.stdout.strip() if pid_result.returncode == 0 else ""

            # 프로세스 이름 가져오기
            process_name = ""
            app_name = ""
            if pid:
                try:
                    comm_result = subprocess.run(
                        ['cat', f'/proc/{pid}/comm'],
                        capture_output=True, text=True, timeout=1
                    )
                    process_name = comm_result.stdout.strip()
                    app_name = process_name
                except:
                    pass

            # WM_CLASS에서 앱 이름 가져오기 (더 정확함)
            try:
                xprop_result = subprocess.run(
                    ['xprop', '-id', window_id, 'WM_CLASS'],
                    capture_output=True, text=True, timeout=1
                )
                if xprop_result.returncode == 0:
                    # WM_CLASS(STRING) = "instance", "class"
                    match = re.search(r'"([^"]+)",\s*"([^"]+)"', xprop_result.stdout)
                    if match:
                        app_name = match.group(2)  # class name 사용
            except:
                pass

            return WindowInfo(
                window_id=window_id,
                title=title,
                app_name=app_name,
                process_name=process_name
            )

        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            # xdotool이 설치되지 않은 경우
            print("Error: xdotool이 설치되어 있지 않습니다.")
            print("설치 명령어: sudo apt install xdotool")
            return None
        except Exception as e:
            print(f"창 정보 가져오기 실패: {e}")
            return None

    def get_current_window(self) -> Optional[WindowInfo]:
        """현재 활성 창 정보 반환"""
        return self._current_window

    @staticmethod
    def activate_window(window_id: str) -> bool:
        """특정 창을 활성화 (포커스 이동)"""
        try:
            subprocess.run(
                ['xdotool', 'windowactivate', window_id],
                capture_output=True, timeout=1
            )
            return True
        except Exception as e:
            print(f"창 활성화 실패: {e}")
            return False

    @staticmethod
    def close_tab(window_id: str) -> bool:
        """현재 탭 닫기 (Ctrl+W 전송)"""
        try:
            # 먼저 해당 창 활성화
            subprocess.run(
                ['xdotool', 'windowactivate', '--sync', window_id],
                capture_output=True, timeout=2
            )
            # Ctrl+W로 탭 닫기
            subprocess.run(
                ['xdotool', 'key', '--window', window_id, 'ctrl+w'],
                capture_output=True, timeout=1
            )
            return True
        except Exception as e:
            print(f"탭 닫기 실패: {e}")
            return False


class AppClassifier:
    """애플리케이션 분류기"""

    def __init__(self, categories: List[dict]):
        """
        Args:
            categories: 카테고리 설정 리스트
                [{"id": "coding", "name": "코딩", "type": "work",
                  "apps": ["code", "vim"], "title_patterns": ["VSCode"]}]
        """
        self.categories = categories

    def classify(self, window: WindowInfo) -> dict:
        """
        창 정보를 기반으로 카테고리 분류

        Returns:
            {"id": str, "name": str, "type": "work"|"entertainment"|"neutral"}
        """
        # 1단계: 창 제목 패턴으로 먼저 매칭 (브라우저 탭 감지용)
        # entertainment를 먼저 체크해서 YouTube 등을 우선 감지
        for category in self.categories:
            if category.get('type') == 'entertainment':
                for pattern in category.get('title_patterns', []):
                    if re.search(pattern, window.title, re.IGNORECASE):
                        return {
                            "id": category['id'],
                            "name": category['name'],
                            "type": category['type']
                        }

        # 2단계: 나머지 카테고리의 창 제목 패턴 매칭
        for category in self.categories:
            if category.get('type') != 'entertainment':
                for pattern in category.get('title_patterns', []):
                    if re.search(pattern, window.title, re.IGNORECASE):
                        return {
                            "id": category['id'],
                            "name": category['name'],
                            "type": category['type']
                        }

        # 3단계: 앱 이름으로 매칭
        app_name_lower = window.app_name.lower()
        process_lower = window.process_name.lower()

        for category in self.categories:
            for app in category.get('apps', []):
                if app.lower() in app_name_lower or app.lower() in process_lower:
                    return {
                        "id": category['id'],
                        "name": category['name'],
                        "type": category['type']
                    }

        # 매칭되지 않으면 neutral 반환
        return {
            "id": "neutral",
            "name": "기타",
            "type": "neutral"
        }
