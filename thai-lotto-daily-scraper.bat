@echo off
cd /d D:\thai-lotto-scraper
echo ===== %DATE% %TIME% ===== >> "D:\thai-lotto-scraper\debug_log.txt"
call "C:\Users\noppa\anaconda3\Scripts\activate.bat" Playground
python "D:\thai-lotto-scraper\thai-lotto-daily-scraper-viewsource.py" >> "D:\thai-lotto-scraper\debug_log.txt" 2>&1
echo. >> "D:\thai-lotto-scraper\debug_log.txt"
