#!/bin/bash
# Focus Guardian 제거 스크립트

echo "🗑️ Focus Guardian을 제거합니다..."

# 데스크톱 엔트리 제거
rm -f ~/.local/share/applications/focus-guardian.desktop
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo "✓ 앱 바로가기 제거 완료"

# 설정 파일 제거 여부 확인
read -p "설정 및 데이터도 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.config/focus-guardian
    echo "✓ 설정 파일 제거 완료"
fi

echo ""
echo "제거가 완료되었습니다."
echo "프로젝트 폴더는 수동으로 삭제해주세요."
