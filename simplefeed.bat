@echo off
call simplefeed_env\Scripts\activate.bat
python simple_feed.py -i terms.csv
if errorlevel 1 (
    echo SimpleFeed encountered an error
) else (
    echo SimpleFeed completed successfully
)
deactivate
