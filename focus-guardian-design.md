# Focus Guardian - 집중력 향상 프로젝트 설계서

## 1. 프로젝트 개요

### 1.1 프로젝트 목표
사용자가 특정 작업 창에서 다른 창으로 전환하려 할 때 토스트 팝업을 통해 인지적 개입을 제공하여, 무의식적인 컨텍스트 스위칭을 방지하고 집중력을 향상시키는 데스크톱 애플리케이션

### 1.2 핵심 가치 제안
- 무의식적인 창 전환 행동에 대한 인지적 개입
- 사용자 맞춤형 집중 시간 설정
- 작업/엔터테인먼트 애플리케이션 분류
- 집중 패턴에 대한 피드백 제공

## 2. 시스템 아키텍처

### 2.1 기술 스택 제안

#### 옵션 1: Electron 기반
```
- Frontend: React + TypeScript
- Backend: Node.js
- UI Framework: Tailwind CSS + shadcn/ui
- 상태 관리: Zustand
- 데이터 저장: SQLite / IndexedDB
- 창 모니터링: native node 모듈 (active-win)
```

#### 옵션 2: Python 기반
```
- GUI: PyQt6 / Tkinter
- 창 모니터링: pygetwindow, pywinauto (Windows), AppKit (macOS)
- 데이터 저장: SQLite
- 시각화: matplotlib
```

### 2.2 시스템 구성 요소

```
┌─────────────────────────────────────────┐
│         Focus Guardian App              │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Window Monitor Service         │  │
│  │   - 활성 창 감지                   │  │
│  │   - 창 전환 이벤트 추적             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Focus Session Manager          │  │
│  │   - 집중 세션 시작/종료            │  │
│  │   - 타이머 관리                    │  │
│  │   - 컨텍스트 스위칭 카운트          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Notification Service           │  │
│  │   - 토스트 팝업 표시               │  │
│  │   - 메시지 커스터마이징             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   App Classifier                 │  │
│  │   - 사용자 정의 앱 분류             │  │
│  │   - 작업/엔터테인먼트 구분          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Analytics & Feedback           │  │
│  │   - 집중 패턴 분석                 │  │
│  │   - 통계 및 시각화                 │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Settings Manager               │  │
│  │   - 사용자 설정 저장/로드           │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

## 3. 핵심 기능 명세

### 3.1 창 모니터링 및 개입

#### 동작 흐름
1. 백그라운드에서 활성 창 모니터링
2. 창 전환 이벤트 감지
3. 전환 조건 평가:
   - 현재 창이 "작업" 카테고리인가?
   - 집중 세션이 활성화되어 있는가?
   - 목표 시간에 도달하지 않았는가?
4. 조건 충족 시 토스트 팝업 표시
5. 사용자 반응 기록

#### 토스트 팝업 메시지 예시
```
- "n분만 더 집중해볼까요? 🎯"
- "거의 다 왔어요! n분만 더 화이팅! 💪"
- "지금 전환하시겠어요? 목표까지 n분 남았습니다"
- "집중 중입니다. 정말 창을 전환하시겠습니까?"
```

#### 팝업 옵션
```
- [계속 집중하기] - 현재 창 유지
- [5분만 더] - 타이머 5분 연장
- [전환하기] - 창 전환 허용 (집중 세션 일시정지)
```

### 3.2 사용자 설정

#### 집중 시간 설정
```typescript
interface FocusSettings {
  defaultDuration: number; // 기본 집중 시간 (분)
  breakInterval: number; // 휴식 간격 (분)
  pomodoroMode: boolean; // 뽀모도로 모드 활성화
  strictMode: boolean; // 엄격 모드 (창 전환 차단)
}
```

#### 앱 분류 설정
```typescript
interface AppCategory {
  id: string;
  name: string;
  type: 'work' | 'entertainment' | 'neutral';
  apps: string[]; // 애플리케이션 이름 또는 프로세스명
  customRules?: {
    urlPatterns?: string[]; // 브라우저용
    titlePatterns?: string[]; // 창 제목 패턴
  };
}

// 예시
const categories: AppCategory[] = [
  {
    id: 'coding',
    name: '코딩',
    type: 'work',
    apps: ['VSCode', 'IntelliJ IDEA', 'PyCharm', 'Visual Studio'],
  },
  {
    id: 'entertainment',
    name: '엔터테인먼트',
    type: 'entertainment',
    apps: ['YouTube', 'Netflix', 'Steam', 'Discord'],
    customRules: {
      urlPatterns: ['youtube.com', 'netflix.com', 'twitch.tv']
    }
  },
  {
    id: 'research',
    name: '조사/학습',
    type: 'work',
    apps: ['Chrome', 'Firefox'],
    customRules: {
      urlPatterns: ['stackoverflow.com', 'github.com', 'documentation.*']
    }
  }
];
```

#### 알림 설정
```typescript
interface NotificationSettings {
  enabled: boolean;
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  duration: number; // 팝업 표시 시간 (초)
  sound: boolean;
  customMessages: string[];
}
```

### 3.3 피드백 및 분석

#### 수집 데이터
```typescript
interface FocusSession {
  id: string;
  startTime: Date;
  endTime?: Date;
  targetDuration: number; // 목표 시간 (분)
  actualDuration: number; // 실제 집중 시간 (분)
  appName: string;
  category: 'work' | 'entertainment' | 'neutral';
  switchAttempts: number; // 창 전환 시도 횟수
  switchesBlocked: number; // 차단된 전환 수
  switchesAllowed: number; // 허용된 전환 수
  completed: boolean; // 목표 달성 여부
}

interface DailyStats {
  date: Date;
  totalFocusTime: number; // 분
  sessionsCompleted: number;
  sessionsAbandoned: number;
  topFocusApps: { app: string; duration: number }[];
  distractionScore: number; // 0-100
}
```

#### 피드백 제공 방식

##### 1. 실시간 피드백
- 세션 종료 시 간단한 요약
- 목표 달성 시 칭찬 메시지
- 연속 달성 기록 (streak)

##### 2. 일일 리포트
```
📊 오늘의 집중 리포트

총 집중 시간: 3시간 25분
완료한 세션: 5개
평균 집중 지속 시간: 41분

🏆 최고 기록
- 최장 집중: VSCode에서 1시간 15분
- 방해 저항: 창 전환 시도 12회 중 9회 방어

💡 인사이트
- 오후 2-4시에 가장 집중력이 높았습니다
- YouTube 전환 시도가 가장 많았습니다 (5회)
```

##### 3. 주간/월간 통계
- 집중 시간 트렌드 그래프
- 가장 집중이 잘 되는 시간대
- 주요 방해 요소 분석
- 카테고리별 시간 분포

##### 4. 시각화 예시
```
집중 시간 트렌드 (주간)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
월 ████████░░ 4h 20m
화 ██████████ 5h 15m
수 ██████░░░░ 3h 45m
목 ████████░░ 4h 30m
금 ██████████ 5h 00m
토 ████░░░░░░ 2h 10m
일 ██░░░░░░░░ 1h 05m

카테고리별 분포
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
코딩        65% ████████████████
문서 작업   20% ██████
조사/학습   15% ████
```

## 4. UI/UX 설계

### 4.1 메인 대시보드

```
┌────────────────────────────────────────────┐
│  Focus Guardian              ⚙️ 설정  ━ ✕  │
├────────────────────────────────────────────┤
│                                            │
│  현재 상태: 집중 중 🎯                       │
│  남은 시간: 23:45                           │
│  ┌──────────────────────────────────────┐ │
│  │ ████████████████░░░░░░░░░░░░░░░░░░  │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  📊 오늘의 통계                             │
│  ┌──────────────────────────────────────┐ │
│  │ 총 집중 시간    3시간 25분             │ │
│  │ 완료 세션       5개                    │ │
│  │ 방어 성공       9/12                   │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  [새 세션 시작]  [휴식 모드]  [통계 보기]   │
│                                            │
└────────────────────────────────────────────┘
```

### 4.2 설정 화면

```
┌────────────────────────────────────────────┐
│  설정                            ← 뒤로가기  │
├────────────────────────────────────────────┤
│                                            │
│  ⏱️ 집중 시간                              │
│  기본 집중 시간    [45] 분                  │
│  휴식 간격        [15] 분                   │
│  □ 뽀모도로 모드                            │
│  □ 엄격 모드 (창 전환 차단)                 │
│                                            │
│  📱 앱 분류                                │
│  ┌──────────────────────────────────────┐ │
│  │ 작업 앱                               │ │
│  │ • VSCode                              │ │
│  │ • IntelliJ IDEA                       │ │
│  │ • Chrome (github.com, stackoverflow)  │ │
│  │ [+ 앱 추가]                            │ │
│  │                                       │ │
│  │ 엔터테인먼트 앱                        │ │
│  │ • YouTube                             │ │
│  │ • Netflix                             │ │
│  │ • Discord                             │ │
│  │ [+ 앱 추가]                            │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  🔔 알림                                   │
│  ☑ 알림 활성화                             │
│  위치: [우측 상단 ▼]                        │
│  표시 시간: [5] 초                          │
│  ☑ 사운드                                  │
│                                            │
│  [저장]                    [기본값으로 복원] │
│                                            │
└────────────────────────────────────────────┘
```

### 4.3 토스트 팝업

```
┌─────────────────────────────────────┐
│  🎯 Focus Guardian                  │
│                                     │
│  23분만 더 집중해볼까요?             │
│  목표까지 거의 다 왔어요!            │
│                                     │
│  [계속 집중] [5분만 더] [전환하기]   │
└─────────────────────────────────────┘
```

## 5. 데이터베이스 스키마

### 5.1 SQLite 스키마

```sql
-- 사용자 설정
CREATE TABLE settings (
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
);

-- 앱 카테고리
CREATE TABLE app_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('work', 'entertainment', 'neutral')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 앱 정의
CREATE TABLE apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id TEXT,
    app_name TEXT NOT NULL,
    process_name TEXT,
    url_pattern TEXT,
    title_pattern TEXT,
    FOREIGN KEY (category_id) REFERENCES app_categories(id)
);

-- 집중 세션
CREATE TABLE focus_sessions (
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
);

-- 창 전환 이벤트
CREATE TABLE switch_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    from_app TEXT,
    to_app TEXT,
    blocked BOOLEAN,
    user_choice TEXT CHECK(user_choice IN ('continue', 'extend', 'switch')),
    FOREIGN KEY (session_id) REFERENCES focus_sessions(id)
);

-- 일일 통계 (집계 테이블)
CREATE TABLE daily_stats (
    date DATE PRIMARY KEY,
    total_focus_time INTEGER,
    sessions_completed INTEGER,
    sessions_abandoned INTEGER,
    distraction_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_sessions_start_time ON focus_sessions(start_time);
CREATE INDEX idx_switch_events_session ON switch_events(session_id);
CREATE INDEX idx_switch_events_timestamp ON switch_events(timestamp);
```

## 6. 구현 단계

### Phase 1: MVP (최소 기능 제품)
- [ ] 창 모니터링 기본 기능
- [ ] 간단한 토스트 팝업
- [ ] 타이머 기능
- [ ] 기본 설정 (집중 시간)
- [ ] 앱 분류 (수동 입력)

### Phase 2: 핵심 기능
- [ ] 완전한 설정 UI
- [ ] 앱 자동 감지 및 분류
- [ ] 브라우저 URL 기반 분류
- [ ] 기본 통계 수집
- [ ] 일일 리포트

### Phase 3: 고급 기능
- [ ] 뽀모도로 모드
- [ ] 엄격 모드 (강제 차단)
- [ ] 상세 분석 대시보드
- [ ] 주간/월간 통계
- [ ] 커스텀 메시지 설정
- [ ] 시각화 차트

### Phase 4: 개선 및 최적화
- [ ] 머신러닝 기반 앱 자동 분류
- [ ] 패턴 인식 (집중 시간대 추천)
- [ ] 목표 설정 및 추적
- [ ] 데이터 내보내기
- [ ] 다크 모드

## 7. 기술적 고려사항

### 7.1 플랫폼별 창 모니터링

#### Windows
```javascript
// Node.js + active-win
const activeWin = require('active-win');

async function monitorActiveWindow() {
    const window = await activeWin();
    console.log(window.title);
    console.log(window.owner.name);
}
```

#### macOS
```python
# Python + AppKit
from AppKit import NSWorkspace

workspace = NSWorkspace.sharedWorkspace()
active_app = workspace.activeApplication()
app_name = active_app['NSApplicationName']
```

#### Linux
```python
# Python + Xlib
from Xlib import display

d = display.Display()
root = d.screen().root
window = root.get_full_property(
    d.intern_atom('_NET_ACTIVE_WINDOW'),
    Xlib.X.AnyPropertyType
).value[0]
```

### 7.2 브라우저 URL 감지

```javascript
// Chrome Extension Manifest V3 (선택적)
{
  "manifest_version": 3,
  "name": "Focus Guardian Browser Helper",
  "permissions": ["tabs", "activeTab"],
  "background": {
    "service_worker": "background.js"
  }
}

// background.js
chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    // URL을 네이티브 앱으로 전송
    sendToNativeApp(tab.url, tab.title);
  });
});
```

### 7.3 성능 최적화

- 창 모니터링 폴링 간격: 500ms - 1s
- 백그라운드 프로세스 메모리 사용량 최소화
- 데이터베이스 쿼리 최적화 (인덱스 활용)
- 일일 통계 사전 집계 (실시간 계산 방지)

### 7.4 보안 및 프라이버시

- 모든 데이터 로컬 저장
- 민감한 창 제목 정보 해시 처리 옵션
- 사용자 동의 없이 데이터 전송 금지
- 데이터 내보내기 시 익명화 옵션

## 8. 사용자 플로우

### 첫 실행 시
1. 환영 화면 및 앱 소개
2. 권한 요청 (창 접근, 알림)
3. 초기 설정 가이드
   - 목표 집중 시간 설정
   - 주요 작업 앱 선택
   - 방해 요소 앱 선택
4. 튜토리얼 (선택사항)

### 일반 사용 플로우
1. 시스템 시작 시 자동 실행
2. 백그라운드에서 조용히 모니터링
3. 작업 앱에서 집중 시작 감지
4. 자동으로 타이머 시작 (또는 수동 시작 옵션)
5. 창 전환 시도 시 개입
6. 세션 종료 시 간단한 피드백
7. 일일 종료 시 리포트 표시

## 9. 향후 확장 가능성

### 기능 확장
- 팀/그룹 챌린지 (친구들과 집중 시간 경쟁)
- 목표 설정 및 보상 시스템
- Notion, Todoist 등 생산성 도구 연동
- 캘린더 연동 (회의 시간 자동 휴식 모드)
- Slack/Discord 상태 자동 업데이트

### AI/ML 기능
- 집중 패턴 학습 및 예측
- 최적 집중 시간 추천
- 방해 요소 자동 감지 및 차단
- 피로도 감지 및 휴식 권장

### 크로스 플랫폼
- 모바일 앱 (스마트폰 사용 모니터링)
- 웹 버전 (브라우저 확장 프로그램)
- 클라우드 동기화

## 10. 성공 지표 (KPI)

### 사용자 행동 지표
- 일일 활성 사용자 (DAU)
- 평균 세션 지속 시간
- 세션 완료율
- 창 전환 차단 성공률

### 효과 지표
- 사용 전/후 집중 시간 비교
- 컨텍스트 스위칭 감소율
- 사용자 만족도 (NPS)
- 지속 사용률 (7일, 30일 retention)

## 11. 참고 자료 및 영감

### 유사 제품
- RescueTime
- Freedom
- Forest
- Cold Turkey
- Focus@Will

### HCI 연구
- Flow State 연구
- Interruption Science
- Digital Wellbeing
- Attention Restoration Theory

## 12. 라이선스 및 배포

### 라이선스 옵션
- MIT License (오픈소스)
- 개인용 무료 / 상업용 유료

### 배포 채널
- GitHub Releases
- Microsoft Store (Windows)
- Mac App Store
- Linux: apt/snap/flatpak

---

**문서 버전**: 1.0
**최종 수정일**: 2025-11-26
**작성자**: Focus Guardian Team
