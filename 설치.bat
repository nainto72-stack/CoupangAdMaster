@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo 필요한 라이브러리를 설치 중입니다...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo 설치가 완료되었습니다. 이제 '실행.bat'이나 바탕화면 아이콘으로 실행하세요.
pause
