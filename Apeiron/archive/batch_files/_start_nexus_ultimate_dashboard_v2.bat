@echo off
title Nexus Dashboard
cd /d "D:\GitHub\Model\PythonApplication1"
echo ========================================
echo    Nexus Dashboard
echo ========================================
echo.
echo streamlit run nexus_ultimate_dashboard_v2.py wordt gestart...
echo.
echo Even geduld, streamlit moet opstarten...
echo.
echo Je zult straks een browser zien openen met:
echo http://localhost:8501
echo.
echo ========================================
streamlit run nexus_ultimate_dashboard_v2.py
echo.
echo ========================================
echo Nexus Dashboard is gestopt.
pause
