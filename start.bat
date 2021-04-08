@echo off
set a=%~s0
cd %a%\..
cls
python blive_record.py
echo.
echo 程序已退出，请按任意键退出...
pause>nul
