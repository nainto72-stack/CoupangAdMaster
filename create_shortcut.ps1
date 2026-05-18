$WScriptShell = New-Object -ComObject WScript.Shell
$TargetPath = "$PSScriptRoot\실행.bat"
$ShortcutFile = "$HOME\Desktop\쿠팡광고분석기.lnk"

$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/c `"$TargetPath`""
$Shortcut.WorkingDirectory = "$PSScriptRoot"
# 아이콘을 파이썬 아이콘으로 설정 (가능한 경우)
$Shortcut.IconLocation = "python.exe"
$Shortcut.Save()

Write-Host "바탕화면에 '쿠팡광고분석기' 바로가기가 생성되었습니다." -ForegroundColor Green
