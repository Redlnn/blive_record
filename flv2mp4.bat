@echo off
if not exist ".\convert" (mkdir convert)
for %%a in (".\download\*.flv") do ffmpeg -i "%%a" -c:v copy -c:a copy ".\convert\%%~na.mp4"
