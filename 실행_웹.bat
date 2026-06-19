@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo 쿠팡 광고 분석기 웹 앱(로컬호스트)을 실행 중입니다...
echo 브라우저가 자동으로 열리지 않으면 http://localhost:8501 로 접속하세요.
streamlit run web_app.py
if %errorlevel% neq 0 (
    echo.
    echo [오류] 웹 앱 실행에 실패했습니다. 라이브러리가 설치되어 있는지 확인해주세요.
    echo '설치.bat'을 실행하여 패키지를 설치한 후 다시 시도해보세요.
    pause
)
