@echo off
%~d0
cd %~s0\..
cls
python blive_record.py
echo.
echo 程序已退出，请按任意键退出...
pause>nul
