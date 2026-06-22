@echo off
chcp 65001 > nul
echo ========================================
echo 쿠팡 광고 최적화 마스터 데스크톱 빌드 시작
echo ========================================

echo 1. PyInstaller 패키지 확인 및 설치 중...
pip install pyinstaller

echo.
echo 2. 빌드 시작 (폴더 형태 배포, 로딩 속도 최적화)...
pyinstaller --noconfirm --onedir --windowed --name "CoupangAdMaster" --collect-all customtkinter app.py

echo.
echo ========================================
echo 빌드가 완료되었습니다!
echo 프로젝트 폴더 내의 [ dist\CoupangAdMaster ] 폴더를 확인하세요.
echo ========================================
