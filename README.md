# Focus Guardian

집중력 향상을 위한 데스크톱 애플리케이션

## 설치 (원클릭)

```bash
cd focus-guardian
./install.sh
```

설치 스크립트가 자동으로:
- 시스템 의존성 설치 (xdotool, libxcb-cursor0)
- Python 가상환경 생성 및 패키지 설치
- 앱 메뉴에 바로가기 생성

## 실행

설치 후 앱 메뉴에서 **"Focus Guardian"** 검색하여 실행

또는 터미널에서:
```bash
./run.sh
```

## 제거

```bash
./uninstall.sh
```

## 기능

- **창 모니터링**: 활성 창을 감지하고 창 전환을 추적
- **집중 세션**: 목표 시간을 설정하고 집중 세션 관리
- **토스트 알림**: 작업 앱에서 엔터테인먼트로 전환 시 알림 표시
- **통계**: 일일 집중 시간, 완료 세션, 방어 성공률 추적

## 프로젝트 구조

```
focus-guardian/
├── src/
│   ├── main.py              # 앱 진입점
│   ├── models/
│   │   └── database.py      # SQLite 데이터베이스
│   ├── services/
│   │   ├── window_monitor.py    # 창 모니터링
│   │   ├── session_manager.py   # 세션 관리
│   │   └── notification.py      # 토스트 알림
│   └── ui/
│       └── main_window.py   # 메인 UI
├── config/
│   └── default_settings.json    # 기본 설정
└── requirements.txt
```
