@echo off
title Nexus Web Interface
cd /d "D:\GitHub\Model\PythonApplication1"
echo ========================================
echo    Nexus Web Interface
echo ========================================
echo.
echo streamlit run nexus_web_interface.py wordt gestart...
echo.
echo Even geduld, streamlit moet opstarten...
echo.
echo Je zult straks een browser zien openen met:
echo http://localhost:8501
echo.
echo ========================================
streamlit run nexus_web_interface.py
echo.
echo ========================================
echo Nexus Web Interface is gestopt.
pause
