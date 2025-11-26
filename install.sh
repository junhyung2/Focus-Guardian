#!/bin/bash
# Focus Guardian 설치 스크립트

set -e

echo "🎯 Focus Guardian 설치를 시작합니다..."

# 현재 스크립트 위치
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="focus-guardian"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 시스템 의존성 확인
echo ""
echo "📦 시스템 의존성 확인 중..."

if ! command -v xdotool &> /dev/null; then
    echo -e "${YELLOW}xdotool이 설치되어 있지 않습니다. 설치합니다...${NC}"
    sudo apt install -y xdotool || {
        echo -e "${RED}xdotool 설치 실패. 수동으로 설치해주세요: sudo apt install xdotool${NC}"
        exit 1
    }
fi

if ! dpkg -l | grep -q libxcb-cursor0; then
    echo -e "${YELLOW}libxcb-cursor0 설치 중...${NC}"
    sudo apt install -y libxcb-cursor0 || true
fi

echo -e "${GREEN}✓ 시스템 의존성 확인 완료${NC}"

# 2. Python 가상환경 생성 및 패키지 설치
echo ""
echo "🐍 Python 환경 설정 중..."

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
fi

source "$SCRIPT_DIR/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo -e "${GREEN}✓ Python 환경 설정 완료${NC}"

# 3. 실행 스크립트 생성
echo ""
echo "📝 실행 스크립트 생성 중..."

cat > "$SCRIPT_DIR/run.sh" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source venv/bin/activate
python src/main.py
EOF

chmod +x "$SCRIPT_DIR/run.sh"

echo -e "${GREEN}✓ 실행 스크립트 생성 완료${NC}"

# 4. 데스크톱 엔트리 생성
echo ""
echo "🖥️ 앱 바로가기 생성 중..."

mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/focus-guardian.desktop << EOF
[Desktop Entry]
Name=Focus Guardian
Comment=집중력 향상 데스크톱 애플리케이션
Exec=$SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/icon.svg
Terminal=false
Type=Application
Categories=Utility;Productivity;
StartupNotify=true
EOF

# 데스크톱 데이터베이스 업데이트
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo -e "${GREEN}✓ 앱 바로가기 생성 완료${NC}"

# 5. 설정 디렉토리 생성
mkdir -p ~/.config/focus-guardian

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Focus Guardian 설치가 완료되었습니다!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "실행 방법:"
echo "  1. 앱 메뉴에서 'Focus Guardian' 검색"
echo "  2. 또는 터미널에서: $SCRIPT_DIR/run.sh"
echo ""
