@echo off
if not exist ".\convert" (mkdir convert)
for %%a in (".\download\*.flv") do ffmpeg -i "%%a" -c copy ".\convert\%%~na.mp4"
