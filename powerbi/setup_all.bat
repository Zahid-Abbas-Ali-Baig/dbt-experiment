@echo off
cd /d "%~dp0.."
python "%~dp0setup_all.py" %*
pause
