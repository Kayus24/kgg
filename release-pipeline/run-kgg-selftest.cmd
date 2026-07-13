@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-kgg-selftest.ps1" %*
exit /b %ERRORLEVEL%
