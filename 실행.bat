@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo 쿠팡 광고 분석기를 실행 중입니다...
python app.py
if %errorlevel% neq 0 (
    echo.
    echo [오류] 프로그램이 비정상 종료되었습니다. 파이썬 환경이나 라이브러리 설치를 확인해주세요.
    pause
)
